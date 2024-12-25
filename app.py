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

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dein-geheimer-schluessel')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///neue_daten.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAPBOX_TOKEN'] = os.environ.get('MAPBOX_TOKEN', 'pk.eyJ1Ijoid2luemVuZHd5ZXJzIiwiYSI6ImNscmx3Z2FtaTBkOHYya3BpbmxnOWFxbXIifQ.qHvhs6vhn6ggAXMg8TA_8g')
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

# Backup bei Serverstart wiederherstellen
try:
    restore_database()
except Exception as e:
    print(f"Fehler beim Wiederherstellen des Backups: {e}")

# Backup bei Serverbeendigung erstellen
atexit.register(backup_database)

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
        
        # Füge Routen hinzu, wenn noch keine existieren
        if Route.query.count() == 0:
            print("Füge initiale Routen hinzu...")
            routes = [
                Route(
                    city='Moers',
                    street='Niephauser Straße',
                    house_numbers='81-165',
                    mobilization_index=3,
                    conviction_index=3,
                    households=None,
                    rental_percentage=None,
                    lat=51.451,
                    lon=6.626,
                    meeting_point="Vor dem Kiosk an der Ecke Niephauser Straße 81",
                    meeting_point_lat=51.451,
                    meeting_point_lon=6.626,
                    is_active=True
                ),
                Route(
                    city='Moers',
                    street='Windmühlenstraße',
                    house_numbers='59-99',
                    mobilization_index=3,
                    conviction_index=3,
                    households=None,
                    rental_percentage=None,
                    lat=51.449,
                    lon=6.623,
                    meeting_point="Am Parkplatz Windmühlenstraße 59",
                    meeting_point_lat=51.449,
                    meeting_point_lon=6.623,
                    is_active=True
                ),
                Route(
                    city='Krefeld',
                    street='Gubener Straße',
                    house_numbers='1-41',
                    mobilization_index=3,
                    conviction_index=3,
                    households=949,
                    rental_percentage=74.6,
                    lat=51.333,
                    lon=6.564,
                    meeting_point="Vor dem Spielplatz Gubener Straße 1",
                    meeting_point_lat=51.333,
                    meeting_point_lon=6.564,
                    is_active=True
                )
            ]
            
            for route in routes:
                db.session.add(route)
            
            db.session.commit()
            print("Initiale Routen wurden hinzugefügt")
        else:
            print("Routen existieren bereits")
        
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
    except Exception as e:
        print(f"Fehler beim Senden der E-Mail: {str(e)}")

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

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001) 