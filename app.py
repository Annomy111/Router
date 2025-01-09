import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime
import sqlite3
import folium
from folium import plugins
import pandas as pd
import numpy as np
from sqlalchemy import func
from models import db, Route, Volunteer, RouteRegistration, WohnquartierAnalyse, User
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from backup_db import backup_database, restore_database
import atexit
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dein-geheimer-schluessel')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.bzqlsaioxqrpcixvdnoo:toCjoz-mockys-gecze8@aws-0-eu-central-1.pooler.supabase.com:6543/postgres?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['GOOGLE_MAPS_KEY'] = 'AIzaSyA80P6QZPiV5Z_dv3sSY9w3igF2XSIIgxA'

# E-Mail-Konfiguration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
app.config['ADMIN_EMAIL'] = os.environ.get('ADMIN_EMAIL', 'Fedo.Hagge-Kubat@fu-berlin.de')

db.init_app(app)
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Erstelle die Datenbank und Tabellen
with app.app_context():
    db.create_all()
    
    # Versuche das Backup wiederherzustellen
    try:
        print("Versuche Backup wiederherzustellen...")
        restore_database()
        print("Backup erfolgreich wiederhergestellt")
        
        # Stelle sicher, dass alle existierenden Routen aktiv sind
        routes = Route.query.all()
        for route in routes:
            if not route.is_active:
                route.is_active = True
        db.session.commit()
        print(f"{len(routes)} Routen wurden aktiviert")
        
    except Exception as e:
        print(f"Fehler beim Wiederherstellen des Backups: {str(e)}")
        print("Fahre mit leerer Datenbank fort...")

# Backup bei Serverbeendigung erstellen
@atexit.register
def create_backup():
    with app.app_context():
        try:
            print("Erstelle Backup...")
            backup_database()
            print("Backup erfolgreich erstellt")
        except Exception as e:
            print(f"Fehler beim Erstellen des Backups: {str(e)}")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin_panel'))
        flash('Ungültige Anmeldedaten')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Keine Berechtigung für diese Seite')
        return redirect(url_for('index'))
        
    stats = {
        'total_routes': Route.query.filter_by(is_active=True).count(),
        'total_volunteers': Volunteer.query.count(),
        'total_registrations': RouteRegistration.query.count(),
        'completion_rate': calculate_completion_rate()
    }
    
    routes = Route.query.all()
    registrations = RouteRegistration.query.order_by(RouteRegistration.date.desc()).all()
    
    return render_template('admin_panel.html', 
                         stats=stats,
                         routes=routes,
                         registrations=registrations)

def calculate_completion_rate():
    total = RouteRegistration.query.count()
    if total == 0:
        return 0
    completed = RouteRegistration.query.filter_by(status='abgeschlossen').count()
    return round((completed / total) * 100)

@app.route('/api/routes/<int:route_id>/toggle', methods=['POST'])
@login_required
def toggle_route_status(route_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
        
    route = Route.query.get_or_404(route_id)
    route.is_active = not route.is_active
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_active': route.is_active,
        'message': f"Route wurde {'aktiviert' if route.is_active else 'deaktiviert'}"
    })

@app.route('/api/registrations/<int:reg_id>/status', methods=['POST'])
@login_required
def update_registration_status(reg_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403
        
    registration = RouteRegistration.query.get_or_404(reg_id)
    data = request.get_json()
    
    if data.get('status') in ['geplant', 'abgeschlossen', 'abgesagt']:
        registration.status = data['status']
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Ungültiger Status'})

def drop_all_tables():
    with app.app_context():
        db.drop_all()
        print("Alle Tabellen wurden gelöscht")

def init_db():
    with app.app_context():
        db.create_all()
        print("Tabellen wurden erstellt")
        
        # Erstelle Admin-Benutzer, wenn noch keiner existiert
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin-Benutzer wurde erstellt")
            print("Username: admin")
            print("Passwort: admin123")
        
        # Prüfe, ob die neuen Routen bereits existieren
        existing_routes = {(r.city, r.street): r for r in Route.query.all()}
        print(f"Gefundene existierende Routen: {len(existing_routes)}")
        
        # Füge neue Routen hinzu
        print("Füge neue Routen hinzu...")
        routes = [
            # Krefeld
            Route(
                city="Krefeld",
                street="Neue Linnerstraße",
                house_numbers="1-50",
                district="Stadtmitte",
                zip_code="47798",
                mobilization_index=3,
                conviction_index=3,
                households=120,
                rental_percentage=85.5,
                lat=51.333,
                lon=6.564,
                meeting_point="Vor dem Café an der Neuen Linnerstraße 1",
                meeting_point_lat=51.333,
                meeting_point_lon=6.564,
                is_active=True
            ),
            Route(
                city="Krefeld",
                street="Marktstraße",
                house_numbers="10-30",
                district="Stadtmitte",
                zip_code="47798",
                mobilization_index=3,
                conviction_index=2,
                households=80,
                rental_percentage=78.3,
                lat=51.334,
                lon=6.565,
                meeting_point="Am Marktplatz",
                meeting_point_lat=51.334,
                meeting_point_lon=6.565,
                is_active=True
            ),
            Route(
                city="Krefeld",
                street="Ostwall",
                house_numbers="1-25",
                district="Stadtmitte",
                zip_code="47798",
                mobilization_index=2,
                conviction_index=3,
                households=95,
                rental_percentage=82.1,
                lat=51.335,
                lon=6.566,
                meeting_point="Vor der Apotheke am Ostwall",
                meeting_point_lat=51.335,
                meeting_point_lon=6.566,
                is_active=True
            ),
            Route(
                city="Krefeld",
                street="Westwall",
                house_numbers="26-50",
                district="Stadtmitte",
                zip_code="47798",
                mobilization_index=3,
                conviction_index=3,
                households=110,
                rental_percentage=75.8,
                lat=51.336,
                lon=6.567,
                meeting_point="An der Bushaltestelle Westwall",
                meeting_point_lat=51.336,
                meeting_point_lon=6.567,
                is_active=True
            ),
            Route(
                city="Krefeld",
                street="Südwall",
                house_numbers="1-40",
                district="Stadtmitte",
                zip_code="47798",
                mobilization_index=2,
                conviction_index=2,
                households=100,
                rental_percentage=71.4,
                lat=51.337,
                lon=6.568,
                meeting_point="Vor dem Kiosk am Südwall",
                meeting_point_lat=51.337,
                meeting_point_lon=6.568,
                is_active=True
            ),
            Route(
                city="Krefeld",
                street="Nordwall",
                house_numbers="15-35",
                district="Stadtmitte",
                zip_code="47798",
                mobilization_index=3,
                conviction_index=2,
                households=85,
                rental_percentage=79.2,
                lat=51.338,
                lon=6.569,
                meeting_point="An der Ecke Nordwall/Hauptstraße",
                meeting_point_lat=51.338,
                meeting_point_lon=6.569,
                is_active=True
            ),
            Route(
                city="Krefeld",
                street="Königstraße",
                house_numbers="1-30",
                district="Stadtmitte",
                zip_code="47798",
                mobilization_index=2,
                conviction_index=3,
                households=90,
                rental_percentage=76.9,
                lat=51.339,
                lon=6.570,
                meeting_point="Vor dem Supermarkt Königstraße",
                meeting_point_lat=51.339,
                meeting_point_lon=6.570,
                is_active=True
            ),
            Route(
                city="Krefeld",
                street="Rheinstraße",
                house_numbers="20-45",
                district="Stadtmitte",
                zip_code="47799",
                mobilization_index=3,
                conviction_index=3,
                households=105,
                rental_percentage=81.5,
                lat=51.340,
                lon=6.571,
                meeting_point="Am Spielplatz Rheinstraße",
                meeting_point_lat=51.340,
                meeting_point_lon=6.571,
                is_active=True
            ),
            Route(
                city="Krefeld",
                street="St.-Anton-Straße",
                house_numbers="1-35",
                district="Stadtmitte",
                zip_code="47799",
                mobilization_index=2,
                conviction_index=2,
                households=95,
                rental_percentage=73.7,
                lat=51.341,
                lon=6.572,
                meeting_point="Vor der Kirche St. Anton",
                meeting_point_lat=51.341,
                meeting_point_lon=6.572,
                is_active=True
            ),
            Route(
                city="Krefeld",
                street="Dreikönigenstraße",
                house_numbers="10-40",
                district="Stadtmitte",
                zip_code="47799",
                mobilization_index=3,
                conviction_index=2,
                households=115,
                rental_percentage=77.8,
                lat=51.342,
                lon=6.573,
                meeting_point="An der Kreuzung Dreikönigenstraße/Rheinstraße",
                meeting_point_lat=51.342,
                meeting_point_lon=6.573,
                is_active=True
            ),

            # Moers
            Route(
                city="Moers",
                street="Neumarkt",
                house_numbers="1-30",
                district="Innenstadt",
                zip_code="47441",
                mobilization_index=3,
                conviction_index=3,
                households=85,
                rental_percentage=72.3,
                lat=51.451,
                lon=6.626,
                meeting_point="Am Neumarkt Brunnen",
                meeting_point_lat=51.451,
                meeting_point_lon=6.626,
                is_active=True
            ),
            Route(
                city="Moers",
                street="Steinstraße",
                house_numbers="15-45",
                district="Innenstadt",
                zip_code="47441",
                mobilization_index=2,
                conviction_index=3,
                households=95,
                rental_percentage=68.9,
                lat=51.452,
                lon=6.627,
                meeting_point="Vor der Buchhandlung Steinstraße",
                meeting_point_lat=51.452,
                meeting_point_lon=6.627,
                is_active=True
            ),
            Route(
                city="Moers",
                street="Homberger Straße",
                house_numbers="1-40",
                district="Innenstadt",
                zip_code="47441",
                mobilization_index=3,
                conviction_index=2,
                households=110,
                rental_percentage=75.4,
                lat=51.453,
                lon=6.628,
                meeting_point="An der Bushaltestelle Homberger Straße",
                meeting_point_lat=51.453,
                meeting_point_lon=6.628,
                is_active=True
            ),
            Route(
                city="Moers",
                street="Haagstraße",
                house_numbers="10-35",
                district="Innenstadt",
                zip_code="47441",
                mobilization_index=2,
                conviction_index=2,
                households=80,
                rental_percentage=71.2,
                lat=51.454,
                lon=6.629,
                meeting_point="Vor dem Café Haagstraße",
                meeting_point_lat=51.454,
                meeting_point_lon=6.629,
                is_active=True
            ),
            Route(
                city="Moers",
                street="Kirchstraße",
                house_numbers="1-25",
                district="Innenstadt",
                zip_code="47441",
                mobilization_index=3,
                conviction_index=3,
                households=70,
                rental_percentage=79.8,
                lat=51.455,
                lon=6.630,
                meeting_point="Vor der Kirche",
                meeting_point_lat=51.455,
                meeting_point_lon=6.630,
                is_active=True
            ),
            Route(
                city="Moers",
                street="Römerstraße",
                house_numbers="20-50",
                district="Innenstadt",
                zip_code="47441",
                mobilization_index=2,
                conviction_index=3,
                households=105,
                rental_percentage=82.5,
                lat=51.456,
                lon=6.631,
                meeting_point="Am Römerbrunnen",
                meeting_point_lat=51.456,
                meeting_point_lon=6.631,
                is_active=True
            ),
            Route(
                city="Moers",
                street="Klosterstraße",
                house_numbers="1-30",
                district="Innenstadt",
                zip_code="47441",
                mobilization_index=3,
                conviction_index=2,
                households=85,
                rental_percentage=74.6,
                lat=51.457,
                lon=6.632,
                meeting_point="Vor dem alten Kloster",
                meeting_point_lat=51.457,
                meeting_point_lon=6.632,
                is_active=True
            ),
            Route(
                city="Moers",
                street="Meerstraße",
                house_numbers="15-40",
                district="Innenstadt",
                zip_code="47441",
                mobilization_index=2,
                conviction_index=2,
                households=90,
                rental_percentage=69.3,
                lat=51.458,
                lon=6.633,
                meeting_point="An der Ecke Meerstraße/Hauptstraße",
                meeting_point_lat=51.458,
                meeting_point_lon=6.633,
                is_active=True
            ),
            Route(
                city="Moers",
                street="Königliche Straße",
                house_numbers="1-35",
                district="Innenstadt",
                zip_code="47441",
                mobilization_index=3,
                conviction_index=3,
                households=95,
                rental_percentage=77.1,
                lat=51.459,
                lon=6.634,
                meeting_point="Vor dem Rathaus",
                meeting_point_lat=51.459,
                meeting_point_lon=6.634,
                is_active=True
            ),
            Route(
                city="Moers",
                street="Friedrichstraße",
                house_numbers="10-45",
                district="Innenstadt",
                zip_code="47441",
                mobilization_index=2,
                conviction_index=3,
                households=100,
                rental_percentage=73.8,
                lat=51.460,
                lon=6.635,
                meeting_point="Am Parkplatz Friedrichstraße",
                meeting_point_lat=51.460,
                meeting_point_lon=6.635,
                is_active=True
            ),

            # Neue Routen für Repelen
            Route(
                city="Moers",
                street="Lerschstraße",
                house_numbers="1-40",
                district="Repelen",
                zip_code="47445",
                mobilization_index=2,
                conviction_index=3,
                households=95,
                rental_percentage=70.5,
                lat=51.471,
                lon=6.646,
                meeting_point="Vor dem Rewe Lerschstraße",
                meeting_point_lat=51.471,
                meeting_point_lon=6.646,
                is_active=True
            ),
            Route(
                city="Moers",
                street="Repelener Straße",
                house_numbers="50-90",
                district="Repelen",
                zip_code="47445",
                mobilization_index=3,
                conviction_index=2,
                households=110,
                rental_percentage=68.2,
                lat=51.472,
                lon=6.647,
                meeting_point="An der Bushaltestelle Repelener Straße",
                meeting_point_lat=51.472,
                meeting_point_lon=6.647,
                is_active=True
            ),
            Route(
                city="Moers",
                street="Baerler Straße",
                house_numbers="15-45",
                district="Repelen",
                zip_code="47445",
                mobilization_index=2,
                conviction_index=2,
                households=85,
                rental_percentage=65.8,
                lat=51.473,
                lon=6.648,
                meeting_point="Vor der Apotheke Baerler Straße",
                meeting_point_lat=51.473,
                meeting_point_lon=6.648,
                is_active=True
            ),
            Route(
                city="Moers",
                street="Schubertstraße",
                house_numbers="1-35",
                district="Repelen",
                zip_code="47445",
                mobilization_index=3,
                conviction_index=3,
                households=75,
                rental_percentage=72.4,
                lat=51.474,
                lon=6.649,
                meeting_point="Am Spielplatz Schubertstraße",
                meeting_point_lat=51.474,
                meeting_point_lon=6.649,
                is_active=True
            ),
            Route(
                city="Moers",
                street="Händelstraße",
                house_numbers="10-40",
                district="Repelen",
                zip_code="47445",
                mobilization_index=2,
                conviction_index=3,
                households=90,
                rental_percentage=69.7,
                lat=51.475,
                lon=6.650,
                meeting_point="An der Kreuzung Händelstraße/Mozartstraße",
                meeting_point_lat=51.475,
                meeting_point_lon=6.650,
                is_active=True
            ),

            # Neue Routen für Meerbeck
            Route(
                city="Moers",
                street="Bismarckstraße",
                house_numbers="20-60",
                district="Meerbeck",
                zip_code="47443",
                mobilization_index=3,
                conviction_index=2,
                households=115,
                rental_percentage=75.8,
                lat=51.476,
                lon=6.651,
                meeting_point="Vor dem Kiosk Bismarckstraße",
                meeting_point_lat=51.476,
                meeting_point_lon=6.651,
                is_active=True
            ),
            Route(
                city="Moers",
                street="Zechenstraße",
                house_numbers="1-45",
                district="Meerbeck",
                zip_code="47443",
                mobilization_index=3,
                conviction_index=3,
                households=105,
                rental_percentage=78.3,
                lat=51.477,
                lon=6.652,
                meeting_point="Am alten Zechengelände",
                meeting_point_lat=51.477,
                meeting_point_lon=6.652,
                is_active=True
            ),
            Route(
                city="Moers",
                street="Lindenstraße",
                house_numbers="10-50",
                district="Meerbeck",
                zip_code="47443",
                mobilization_index=2,
                conviction_index=2,
                households=95,
                rental_percentage=73.6,
                lat=51.478,
                lon=6.653,
                meeting_point="Vor der Bäckerei Lindenstraße",
                meeting_point_lat=51.478,
                meeting_point_lon=6.653,
                is_active=True
            ),
            Route(
                city="Moers",
                street="Barbarastraße",
                house_numbers="5-35",
                district="Meerbeck",
                zip_code="47443",
                mobilization_index=3,
                conviction_index=2,
                households=85,
                rental_percentage=76.2,
                lat=51.479,
                lon=6.654,
                meeting_point="An der Bushaltestelle Barbarastraße",
                meeting_point_lat=51.479,
                meeting_point_lon=6.654,
                is_active=True
            ),
            Route(
                city="Moers",
                street="Kampstraße",
                house_numbers="15-55",
                district="Meerbeck",
                zip_code="47443",
                mobilization_index=2,
                conviction_index=3,
                households=100,
                rental_percentage=74.5,
                lat=51.480,
                lon=6.655,
                meeting_point="Vor dem Supermarkt Kampstraße",
                meeting_point_lat=51.480,
                meeting_point_lon=6.655,
                is_active=True
            ),

            # Neukirchen-Vluyn
            Route(
                city="Neukirchen-Vluyn",
                street="Hochstraße",
                house_numbers="1-35",
                district="Neukirchen",
                zip_code="47506",
                mobilization_index=3,
                conviction_index=2,
                households=90,
                rental_percentage=65.7,
                lat=51.461,
                lon=6.636,
                meeting_point="Vor dem Café Hochstraße",
                meeting_point_lat=51.461,
                meeting_point_lon=6.636,
                is_active=True
            ),
            Route(
                city="Neukirchen-Vluyn",
                street="Niederrheinallee",
                house_numbers="10-40",
                district="Neukirchen",
                zip_code="47506",
                mobilization_index=2,
                conviction_index=3,
                households=95,
                rental_percentage=68.4,
                lat=51.462,
                lon=6.637,
                meeting_point="An der Bushaltestelle Niederrheinallee",
                meeting_point_lat=51.462,
                meeting_point_lon=6.637,
                is_active=True
            ),
            Route(
                city="Neukirchen-Vluyn",
                street="Andreas-Bräm-Straße",
                house_numbers="1-30",
                district="Neukirchen",
                zip_code="47506",
                mobilization_index=3,
                conviction_index=3,
                households=80,
                rental_percentage=71.9,
                lat=51.463,
                lon=6.638,
                meeting_point="Vor der Andreas-Bräm-Schule",
                meeting_point_lat=51.463,
                meeting_point_lon=6.638,
                is_active=True
            ),
            Route(
                city="Neukirchen-Vluyn",
                street="Mozartstraße",
                house_numbers="15-45",
                district="Vluyn",
                zip_code="47506",
                mobilization_index=2,
                conviction_index=2,
                households=85,
                rental_percentage=63.5,
                lat=51.464,
                lon=6.639,
                meeting_point="Am Musikpavillon",
                meeting_point_lat=51.464,
                meeting_point_lon=6.639,
                is_active=True
            ),
            Route(
                city="Neukirchen-Vluyn",
                street="Vluyner Platz",
                house_numbers="1-25",
                district="Vluyn",
                zip_code="47506",
                mobilization_index=3,
                conviction_index=2,
                households=70,
                rental_percentage=69.2,
                lat=51.465,
                lon=6.640,
                meeting_point="Am Vluyner Platz Brunnen",
                meeting_point_lat=51.465,
                meeting_point_lon=6.640,
                is_active=True
            ),
            Route(
                city="Neukirchen-Vluyn",
                street="Pastoratstraße",
                house_numbers="20-50",
                district="Neukirchen",
                zip_code="47506",
                mobilization_index=2,
                conviction_index=3,
                households=100,
                rental_percentage=66.8,
                lat=51.466,
                lon=6.641,
                meeting_point="Vor der Kirche",
                meeting_point_lat=51.466,
                meeting_point_lon=6.641,
                is_active=True
            ),
            Route(
                city="Neukirchen-Vluyn",
                street="Krefelder Straße",
                house_numbers="1-40",
                district="Vluyn",
                zip_code="47506",
                mobilization_index=3,
                conviction_index=3,
                households=95,
                rental_percentage=72.4,
                lat=51.467,
                lon=6.642,
                meeting_point="An der Kreuzung Krefelder Straße/Hauptstraße",
                meeting_point_lat=51.467,
                meeting_point_lon=6.642,
                is_active=True
            ),
            Route(
                city="Neukirchen-Vluyn",
                street="Geldernsche Straße",
                house_numbers="10-35",
                district="Neukirchen",
                zip_code="47506",
                mobilization_index=2,
                conviction_index=2,
                households=85,
                rental_percentage=64.3,
                lat=51.468,
                lon=6.643,
                meeting_point="Vor dem Supermarkt",
                meeting_point_lat=51.468,
                meeting_point_lon=6.643,
                is_active=True
            ),
            Route(
                city="Neukirchen-Vluyn",
                street="Wiesfurthstraße",
                house_numbers="1-30",
                district="Vluyn",
                zip_code="47506",
                mobilization_index=3,
                conviction_index=2,
                households=80,
                rental_percentage=67.9,
                lat=51.469,
                lon=6.644,
                meeting_point="Am Spielplatz Wiesfurth",
                meeting_point_lat=51.469,
                meeting_point_lon=6.644,
                is_active=True
            ),
            Route(
                city="Neukirchen-Vluyn",
                street="Ernst-Moritz-Arndt-Straße",
                house_numbers="15-40",
                district="Neukirchen",
                zip_code="47506",
                mobilization_index=2,
                conviction_index=3,
                households=90,
                rental_percentage=70.5,
                lat=51.470,
                lon=6.645,
                meeting_point="An der Bushaltestelle Ernst-Moritz-Arndt-Straße",
                meeting_point_lat=51.470,
                meeting_point_lon=6.645,
                is_active=True
            )
        ]
        
        new_routes_count = 0
        for route in routes:
            key = (route.city, route.street)
            if key not in existing_routes:
                db.session.add(route)
                new_routes_count += 1
                print(f"Neue Route hinzugefügt: {route.street} {route.house_numbers}")
        
        if new_routes_count > 0:
            db.session.commit()
            print(f"✓ {new_routes_count} neue Routen wurden hinzugefügt")
        else:
            print("Keine neuen Routen hinzugefügt")
        
        print("Datenbankinitialisierung abgeschlossen")

def send_registration_notification(volunteer, route, registration):
    """Sendet eine E-Mail-Benachrichtigung über eine neue Routenregistrierung"""
    try:
        subject = f"Neue Routenregistrierung: {route.street}"
        body = f"""
Neue Routenregistrierung eingegangen:

Freiwilliger:
- Name: {volunteer.name}
- E-Mail: {volunteer.email}
- Telefon: {volunteer.phone or 'Nicht angegeben'}

Route:
- Stadt: {route.city}
- Straße: {route.street}
- Hausnummern: {route.house_numbers}

Termin:
- Datum: {registration.date.strftime('%d.%m.%Y')}
- Zeitfenster: {registration.time_slot}

Status: {registration.status}
"""
        msg = Message(
            subject=subject,
            recipients=[app.config['ADMIN_EMAIL']],
            body=body
        )
        mail.send(msg)
        print(f"Benachrichtigungs-E-Mail wurde an {app.config['ADMIN_EMAIL']} gesendet")
        
        # Sende auch eine Bestätigungs-E-Mail an den Freiwilligen
        send_volunteer_confirmation(volunteer, route, registration)
        
    except Exception as e:
        print(f"Fehler beim Senden der E-Mail: {str(e)}")

def send_volunteer_confirmation(volunteer, route, registration):
    """Sendet eine Bestätigungs-E-Mail an den Freiwilligen"""
    try:
        subject = "Bestätigung Ihrer Anmeldung für den Haustürwahlkampf"
        
        # HTML-Version der E-Mail
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #DC3545;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }}
        .content {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 0 0 5px 5px;
        }}
        .info-box {{
            background-color: white;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
            border-left: 4px solid #DC3545;
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            font-size: 0.9em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Vielen Dank für Ihre Anmeldung!</h1>
        </div>
        <div class="content">
            <p>Hallo {volunteer.name},</p>
            
            <p>vielen Dank für Ihre Anmeldung zum Haustürwahlkampf. Wir freuen uns sehr über Ihr Engagement!</p>
            
            <div class="info-box">
                <h3>Ihre Routendetails:</h3>
                <p><strong>Stadt:</strong> {route.city}<br>
                <strong>Straße:</strong> {route.street}<br>
                <strong>Hausnummern:</strong> {route.house_numbers}<br>
                <strong>Datum:</strong> {registration.date.strftime('%d.%m.%Y')}<br>
                <strong>Zeitfenster:</strong> {registration.time_slot}</p>
            </div>
            
            <div class="info-box">
                <h3>Wichtige Informationen:</h3>
                <ul>
                    <li>Bitte seien Sie 5-10 Minuten vor Beginn am Treffpunkt</li>
                    <li>Treffpunkt: {route.meeting_point}</li>
                    <li>Sie erhalten vor Ort alle notwendigen Materialien</li>
                    <li>Bitte bringen Sie einen Stift und ggf. eine Wasserflasche mit</li>
                    <li>Bei schlechtem Wetter: Denken Sie an einen Regenschirm</li>
                </ul>
            </div>
            
            <p>Falls Sie Fragen haben oder den Termin nicht wahrnehmen können, melden Sie sich bitte unter {app.config['ADMIN_EMAIL']}.</p>
            
            <p>Wir freuen uns auf Sie!</p>
            
            <p>Mit besten Grüßen<br>
            Ihr Team Dieren</p>
        </div>
        <div class="footer">
            <p>Diese E-Mail wurde automatisch generiert. Bitte antworten Sie nicht direkt auf diese E-Mail.</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Text-Version der E-Mail für E-Mail-Clients, die kein HTML unterstützen
        text_body = f"""
Vielen Dank für Ihre Anmeldung zum Haustürwahlkampf!

Hallo {volunteer.name},

vielen Dank für Ihre Anmeldung zum Haustürwahlkampf. Wir freuen uns sehr über Ihr Engagement!

Ihre Routendetails:
- Stadt: {route.city}
- Straße: {route.street}
- Hausnummern: {route.house_numbers}
- Datum: {registration.date.strftime('%d.%m.%Y')}
- Zeitfenster: {registration.time_slot}
- Treffpunkt: {route.meeting_point}

Wichtige Informationen:
- Bitte seien Sie 5-10 Minuten vor Beginn am Treffpunkt
- Sie erhalten vor Ort alle notwendigen Materialien
- Bitte bringen Sie einen Stift und ggf. eine Wasserflasche mit
- Bei schlechtem Wetter: Denken Sie an einen Regenschirm

Falls Sie Fragen haben oder den Termin nicht wahrnehmen können, melden Sie sich bitte unter {app.config['ADMIN_EMAIL']}.

Wir freuen uns auf Sie!

Mit besten Grüßen
Ihr Team Dieren

---
Diese E-Mail wurde automatisch generiert. Bitte antworten Sie nicht direkt auf diese E-Mail.
"""
        
        msg = Message(
            subject=subject,
            recipients=[volunteer.email],
            body=text_body,
            html=html_body
        )
        mail.send(msg)
        print(f"Bestätigungs-E-Mail wurde an {volunteer.email} gesendet")
        
    except Exception as e:
        print(f"Fehler beim Senden der Bestätigungs-E-Mail: {str(e)}")

@app.route('/')
def index():
    # Nur aktive Routen anzeigen
    routes = Route.query.filter_by(is_active=True).all()
    
    # Gruppiere Routen nach Stadt
    cities = {}
    for route in routes:
        if route.city not in cities:
            cities[route.city] = []
        cities[route.city].append(route)
    
    return render_template('index.html', cities=cities, routes=routes)

@app.route('/karte')
def map_view():
    return render_template('map.html', google_maps_key=app.config['GOOGLE_MAPS_KEY'])

@app.route('/api/routes')
def get_routes():
    routes = Route.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': route.id,
        'city': route.city,
        'street': route.street,
        'house_numbers': route.house_numbers,
        'mobilization_index': route.mobilization_index,
        'conviction_index': route.conviction_index,
        'lat': route.lat,
        'lon': route.lon,
        'meeting_point': route.meeting_point,
        'meeting_point_lat': route.meeting_point_lat,
        'meeting_point_lon': route.meeting_point_lon
    } for route in routes])

@app.route('/route/<int:route_id>')
def route_detail(route_id):
    route = Route.query.get_or_404(route_id)
    registrations = RouteRegistration.query.filter_by(route_id=route_id).all()
    mapbox_token = app.config['MAPBOX_TOKEN']
    return render_template('route_detail.html', 
                         route=route, 
                         registrations=registrations,
                         google_maps_key=app.config['GOOGLE_MAPS_KEY'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        route_id = request.form.get('route_id')
        route = Route.query.get_or_404(route_id)
        
        # Prüfe verfügbare Plätze
        stats = route.get_registration_stats()
        if stats['available_slots'] <= 0:
            flash('Diese Route ist bereits voll besetzt. Bitte wählen Sie eine andere Route.', 'danger')
            return redirect(url_for('register'))

        # Erstelle neuen Freiwilligen
        volunteer = Volunteer(
            name=request.form.get('name'),
            email=request.form.get('email'),
            phone=request.form.get('phone')
        )
        
        try:
            db.session.add(volunteer)
            db.session.flush()  # Generiere ID für den Freiwilligen
            
            # Erstelle Registrierung
            registration = RouteRegistration(
                volunteer_id=volunteer.id,
                route_id=route_id,
                date=datetime.strptime(request.form.get('date'), '%Y-%m-%d'),
                time_slot=request.form.get('time_slot'),
                status='geplant'
            )
            
            db.session.add(registration)
            db.session.commit()
            
            # Sende Benachrichtigungen
            send_registration_notification(volunteer, route, registration)
            
            flash('Ihre Registrierung wurde erfolgreich gespeichert!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ein Fehler ist aufgetreten: {str(e)}', 'danger')
            return redirect(url_for('register'))
    
    routes = Route.query.all()
    now = datetime.now()
    return render_template('register.html', routes=routes, now=now)

@app.route('/api/route-data')
def route_data():
    routes = Route.query.all()
    data = [{
        'id': r.id,
        'city': r.city,
        'street': r.street,
        'house_numbers': r.house_numbers,
        'mobilization_index': r.mobilization_index,
        'conviction_index': r.conviction_index,
        'households': r.households,
        'rental_percentage': r.rental_percentage,
        'registrations_count': len(r.registrations)
    } for r in routes]
    return jsonify(data)

@app.route('/routen-analyse')
def route_analysis():
    try:
        # Verbinde die Tabellen wohnquartier und excel_data
        sql_query = """
        SELECT 
            w.Gemeinde,
            w.Haushalte,
            w.Haushalte_zur_Miete,
            w.Haushalte_mit_Kindern,
            e.STRASSE_NAME,
            e.HAUSNR_ANFANG,
            e.HAUSNR_ENDE,
            e.MOBILISIERUNGSINDEX_KLASSE_WKR,
            e.UEBERZEUGUNSINDEX_KLASSE_WKR
        FROM wohnquartier w
        JOIN excel_data e ON w.Gemeinde = e.GEMEINDE_NAME
        WHERE w.Haushalte IS NOT NULL
        """
        
        result = db.session.execute(sql_query)
        rows = result.fetchall()
        
        analyzed_data = []
        gemeinde_data = {}
        
        for row in rows:
            gemeinde = row.Gemeinde
            
            if gemeinde not in gemeinde_data:
                gemeinde_data[gemeinde] = {
                    'Haushalte': 0,
                    'Haushalte_zur_Miete': 0,
                    'Haushalte_mit_Kindern': 0,
                    'Mobilisierung_Sum': 0,
                    'Ueberzeugung_Sum': 0,
                    'Anzahl': 0,
                    'Strassen': set()
                }
            
            gd = gemeinde_data[gemeinde]
            gd['Haushalte'] += row.Haushalte or 0
            gd['Haushalte_zur_Miete'] += row.Haushalte_zur_Miete or 0
            gd['Haushalte_mit_Kindern'] += row.Haushalte_mit_Kindern or 0
            gd['Mobilisierung_Sum'] += row.MOBILISIERUNGSINDEX_KLASSE_WKR or 0
            gd['Ueberzeugung_Sum'] += row.UEBERZEUGUNSINDEX_KLASSE_WKR or 0
            gd['Anzahl'] += 1
            if row.STRASSE_NAME:
                gd['Strassen'].add(row.STRASSE_NAME)
            
            # Berechne Scores für einzelnes Wohnquartier
            if row.Haushalte and row.Haushalte > 0:
                mietquote = (row.Haushalte_zur_Miete or 0) / row.Haushalte * 100
                kinderquote = (row.Haushalte_mit_Kindern or 0) / row.Haushalte * 100
                mobilisierung = row.MOBILISIERUNGSINDEX_KLASSE_WKR or 0
                ueberzeugung = row.UEBERZEUGUNSINDEX_KLASSE_WKR or 0
                
                potential_score = (
                    (mietquote / 100 * 0.3) +  # Mietquote (30%)
                    (kinderquote / 100 * 0.2) +  # Kinderquote (20%)
                    (mobilisierung / 3 * 0.25) +  # Mobilisierung (25%)
                    (ueberzeugung / 3 * 0.25)  # Überzeugung (25%)
                ) * 3  # Skalierung auf 0-3
                
                analyzed_data.append({
                    'Gemeinde': gemeinde,
                    'Strasse': row.STRASSE_NAME,
                    'Hausnummern': f"{row.HAUSNR_ANFANG}-{row.HAUSNR_ENDE}" if row.HAUSNR_ANFANG else "",
                    'Haushalte': row.Haushalte,
                    'Mietquote': mietquote,
                    'Kinderquote': kinderquote,
                    'Mobilisierung': mobilisierung,
                    'Ueberzeugung': ueberzeugung,
                    'potential_score': potential_score
                })
        
        # Berechne Durchschnitte für jede Gemeinde
        areas = {}
        for gemeinde, gd in gemeinde_data.items():
            if gd['Anzahl'] > 0:
                areas[gemeinde] = {
                    'data': [],
                    'stats': {
                        'total_households': gd['Haushalte'],
                        'avg_rent_quota': (gd['Haushalte_zur_Miete'] / gd['Haushalte'] * 100) if gd['Haushalte'] > 0 else 0,
                        'avg_children_quota': (gd['Haushalte_mit_Kindern'] / gd['Haushalte'] * 100) if gd['Haushalte'] > 0 else 0,
                        'avg_mobilisierung': gd['Mobilisierung_Sum'] / gd['Anzahl'],
                        'avg_ueberzeugung': gd['Ueberzeugung_Sum'] / gd['Anzahl'],
                        'total_districts': gd['Anzahl'],
                        'total_streets': len(gd['Strassen'])
                    }
                }
                
                # Berechne durchschnittliches Potenzial
                areas[gemeinde]['stats']['avg_potential'] = (
                    (areas[gemeinde]['stats']['avg_rent_quota'] / 100 * 0.3) +
                    (areas[gemeinde]['stats']['avg_children_quota'] / 100 * 0.2) +
                    (areas[gemeinde]['stats']['avg_mobilisierung'] / 3 * 0.25) +
                    (areas[gemeinde]['stats']['avg_ueberzeugung'] / 3 * 0.25)
                ) * 3
        
        # Sortiere die Daten
        top_potential = sorted(analyzed_data, key=lambda x: x['potential_score'], reverse=True)
        top_households = sorted(analyzed_data, key=lambda x: x['Haushalte'], reverse=True)
        
        print(f"Gefundene Gemeinden: {list(areas.keys())}")
        print(f"Anzahl Datensätze: {len(analyzed_data)}")
        
        return render_template('route_analysis.html',
                             areas=areas,
                             top_potential=top_potential[:10],
                             top_households=top_households[:10],
                             total_data=analyzed_data)
                             
    except Exception as e:
        print(f"Fehler in route_analysis: {str(e)}")
        return render_template('route_analysis.html',
                             areas={},
                             top_potential=[],
                             top_households=[],
                             total_data=[],
                             error=str(e))

@app.route('/freiwilligen-dashboard')
def volunteer_dashboard():
    volunteers = Volunteer.query.all()
    
    # Berechne Statistiken für jeden Freiwilligen
    for volunteer in volunteers:
        volunteer.total_routes = len(volunteer.registrations)
        volunteer.upcoming_routes = len([r for r in volunteer.registrations 
                                      if r.date >= datetime.now()])
        volunteer.completed_routes = len([r for r in volunteer.registrations 
                                       if r.status == 'abgeschlossen'])
    
    return render_template('volunteer_dashboard.html',
                         volunteers=volunteers)

@app.route('/kalender')
def calendar():
    calendar_url = "https://calendar.google.com/calendar/embed?src=nvf3q8gvcrtm7ed3kfupcc0j78%40group.calendar.google.com&ctz=Europe%2FBerlin"
    return render_template('calendar.html', calendar_url=calendar_url)

@app.route('/api/routes/<int:route_id>/path', methods=['POST'])
def save_route_path(route_id):
    route = Route.query.get_or_404(route_id)
    data = request.get_json()
    
    if 'coordinates' in data:
        route.path_coordinates = data['coordinates']
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Keine Koordinaten gefunden'}), 400

@app.route('/api/register', methods=['POST'])
def register_route():
    data = request.get_json()
    
    # Erstelle oder hole den Freiwilligen
    volunteer = Volunteer.query.filter_by(email=data['email']).first()
    if not volunteer:
        volunteer = Volunteer(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone')
        )
        db.session.add(volunteer)
    
    # Hole die Route
    route = Route.query.get_or_404(data['route_id'])
    
    # Erstelle die Registrierung
    registration = RouteRegistration(
        route=route,
        volunteer=volunteer,
        date=datetime.strptime(data['date'], '%Y-%m-%d'),
        time_slot=data['time_slot'],
        status='geplant'
    )
    
    try:
        db.session.add(registration)
        db.session.commit()
        
        # Sende Benachrichtigungs-E-Mail
        send_registration_notification(volunteer, route, registration)
        
        return jsonify({
            'success': True,
            'message': 'Registrierung erfolgreich'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.after_request
def add_security_headers(response):
    if response.mimetype == 'text/html':
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://maps.googleapis.com https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https://*.googleapis.com https://*.gstatic.com; "
            "connect-src 'self' https://*.googleapis.com; "
            "frame-src 'self'; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "object-src 'none';"
        )
    return response

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001) 