import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sqlite3
import folium
from folium import plugins
import pandas as pd
import numpy as np
from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dein-geheimer-schluessel')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///neue_daten.db'
app.config['MAPBOX_TOKEN'] = os.environ.get('MAPBOX_TOKEN', 'pk.eyJ1Ijoid2luemVuZHd5ZXJzIiwiYSI6ImNscmx3Z2FtaTBkOHYya3BpbmxnOWFxbXIifQ.qHvhs6vhn6ggAXMg8TA_8g')

if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)

db = SQLAlchemy(app)

# Datenbankmodelle
class Volunteer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    registrations = db.relationship('RouteRegistration', backref='volunteer', lazy=True)

class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    street = db.Column(db.String(100), nullable=False)
    house_numbers = db.Column(db.String(100), nullable=False)
    mobilization_index = db.Column(db.Integer, nullable=False)
    conviction_index = db.Column(db.Integer, nullable=False)
    households = db.Column(db.Integer)
    rental_percentage = db.Column(db.Float)
    lat = db.Column(db.Float)  # Breitengrad
    lon = db.Column(db.Float)  # Längengrad
    registrations = db.relationship('RouteRegistration', backref='route', lazy=True)

class RouteRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    volunteer_id = db.Column(db.Integer, db.ForeignKey('volunteer.id'), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('route.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    time_slot = db.Column(db.String(20), nullable=False)  # z.B. "17:00-19:00"
    status = db.Column(db.String(20), default='geplant')  # geplant, abgeschlossen, abgesagt

class WohnquartierAnalyse(db.Model):
    __tablename__ = 'wohnquartier'
    
    # Eigener Primärschlüssel
    id = db.Column(db.Integer, primary_key=True)
    Gemeinde = db.Column(db.String)
    Haushalte = db.Column(db.Integer)
    Haushalte_zur_Miete = db.Column(db.Float)
    Haushalte_mit_Kindern = db.Column(db.Float)
    
    # Neue Felder für Wahlkreis- und Quartiersdetails
    WKR_SCHLUESSEL = db.Column(db.String)
    WKR_NAME = db.Column(db.String)
    WOHNQUART_SCHLUESSEL = db.Column(db.String)
    MOBILISIERUNGSINDEX_KLASSE_WKR = db.Column(db.Integer)
    UEBERZEUGUNSINDEX_KLASSE_WKR = db.Column(db.Integer)
    
    def calculate_scores(self):
        """Berechnet verschiedene Scoring-Werte für das Wohnquartier"""
        if not self.Haushalte or self.Haushalte <= 0:
            return {
                'mietquote': 0,
                'kinderquote': 0,
                'potential_score': 0
            }
        
        # Grundlegende Quoten
        mietquote = (self.Haushalte_zur_Miete or 0) / self.Haushalte * 100
        kinderquote = (self.Haushalte_mit_Kindern or 0) / self.Haushalte * 100
        
        # Gewichteter Score basierend auf den verfügbaren Daten
        potential_score = (
            mietquote / 100 * 0.4 +              # Mietquote (40%)
            (kinderquote / 100) * 0.3 +          # Kinderquote (30%)
            (self.MOBILISIERUNGSINDEX_KLASSE_WKR or 0) / 3 * 0.3  # Mobilisierungsindex (30%)
        )
        
        return {
            'mietquote': mietquote,
            'kinderquote': kinderquote,
            'potential_score': potential_score,
            'mobilisierung': self.MOBILISIERUNGSINDEX_KLASSE_WKR,
            'ueberzeugung': self.UEBERZEUGUNSINDEX_KLASSE_WKR
        }

def init_db():
    with app.app_context():
        db.create_all()
        
        # Füge Routen hinzu, wenn noch keine existieren
        if Route.query.count() == 0:
            routes = [
                Route(
                    city='Moers',
                    street='Niephauser Straße',
                    house_numbers='81-165',
                    mobilization_index=3,
                    conviction_index=3,
                    households=None,  # Wird aus der DB geladen
                    rental_percentage=None,  # Wird aus der DB geladen
                    lat=51.451,  # Beispielkoordinaten
                    lon=6.626
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
                    lon=6.623
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
                    lon=6.564
                ),
                Route(
                    city='Krefeld',
                    street='Breslauer Straße',
                    house_numbers='1-31',
                    mobilization_index=3,
                    conviction_index=3,
                    households=949,
                    rental_percentage=74.6,
                    lat=51.335,
                    lon=6.568
                )
            ]
            for route in routes:
                db.session.add(route)
            db.session.commit()

@app.route('/')
def index():
    routes = Route.query.all()
    return render_template('index.html', routes=routes)

@app.route('/karte')
def map_view():
    routes = Route.query.all()
    
    # Erstelle Karte zentriert auf Moers
    m = folium.Map(location=[51.451, 6.626], zoom_start=11)
    
    # Füge Marker für jede Route hinzu
    for route in routes:
        popup_text = f"""
            <b>{route.street} {route.house_numbers}</b><br>
            {route.city}<br>
            Mobilisierungsindex: {route.mobilization_index}/3<br>
            Überzeugungsindex: {route.conviction_index}/3<br>
            """
        if route.households:
            popup_text += f"Haushalte: {route.households}<br>"
        if route.rental_percentage:
            popup_text += f"Mietquote: {route.rental_percentage:.1f}%<br>"
            
        folium.Marker(
            [route.lat, route.lon],
            popup=popup_text,
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
    
    return m._repr_html_()

@app.route('/route/<int:route_id>')
def route_detail(route_id):
    route = Route.query.get_or_404(route_id)
    registrations = RouteRegistration.query.filter_by(route_id=route_id).all()
    mapbox_token = app.config['MAPBOX_TOKEN']
    return render_template('route_detail.html', 
                         route=route, 
                         registrations=registrations,
                         mapbox_token=mapbox_token)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        route_id = request.form.get('route_id')
        date = request.form.get('date')
        time_slot = request.form.get('time_slot')
        
        # Prüfe ob Freiwilliger bereits existiert
        volunteer = Volunteer.query.filter_by(email=email).first()
        if not volunteer:
            volunteer = Volunteer(name=name, email=email, phone=phone)
            db.session.add(volunteer)
            db.session.commit()
        
        # Erstelle neue Routenregistrierung
        registration = RouteRegistration(
            volunteer_id=volunteer.id,
            route_id=route_id,
            date=datetime.strptime(date, '%Y-%m-%d'),
            time_slot=time_slot
        )
        db.session.add(registration)
        db.session.commit()
        
        flash('Vielen Dank für deine Registrierung!', 'success')
        return redirect(url_for('route_detail', route_id=route_id))
    
    routes = Route.query.all()
    return render_template('register.html', routes=routes, now=datetime.now())

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
    # Hole alle Wohnquartiere mit nicht-null Haushalten
    wohnquartiere = WohnquartierAnalyse.query.filter(WohnquartierAnalyse.Haushalte.isnot(None)).all()
    analyzed_data = []
    
    # Gruppiere die Daten nach Gemeinde
    gemeinde_data = {}
    for wq in wohnquartiere:
        if wq.Gemeinde not in gemeinde_data:
            gemeinde_data[wq.Gemeinde] = {
                'Haushalte': 0,
                'Haushalte_zur_Miete': 0,
                'Haushalte_mit_Kindern': 0,
                'Anzahl': 0
            }
        
        gd = gemeinde_data[wq.Gemeinde]
        gd['Haushalte'] += wq.Haushalte or 0
        gd['Haushalte_zur_Miete'] += wq.Haushalte_zur_Miete or 0
        gd['Haushalte_mit_Kindern'] += wq.Haushalte_mit_Kindern or 0
        gd['Anzahl'] += 1
    
    # Erstelle aggregierte Analyseobjekte
    for gemeinde, gd in gemeinde_data.items():
        if gd['Haushalte'] > 0:
            mietquote = (gd['Haushalte_zur_Miete'] / gd['Haushalte']) * 100
            kinderquote = (gd['Haushalte_mit_Kindern'] / gd['Haushalte']) * 100
            potential_score = (mietquote / 100 * 0.6) + (kinderquote / 100 * 0.4)
            
            data = {
                'Gemeinde': gemeinde,
                'Haushalte': gd['Haushalte'],
                'Mietquote': mietquote,
                'Kinderquote': kinderquote,
                'potential_score': potential_score
            }
            analyzed_data.append(data)
    
    # Gruppiere nach Stadtteilen für die Übersicht
    areas = {}
    for data in analyzed_data:
        area = data['Gemeinde']
        if area not in areas:
            areas[area] = {
                'data': [],
                'stats': {
                    'total_households': 0,
                    'avg_potential': 0,
                    'avg_rent_quota': 0,
                    'avg_children_quota': 0,
                    'total_districts': 0
                }
            }
        
        areas[area]['data'].append(data)
        stats = areas[area]['stats']
        stats['total_households'] += data['Haushalte'] or 0
        stats['avg_potential'] += data['potential_score']
        stats['avg_rent_quota'] += data['Mietquote']
        stats['avg_children_quota'] += data['Kinderquote']
        stats['total_districts'] += 1
    
    # Berechne Durchschnitte
    for area in areas:
        stats = areas[area]['stats']
        count = stats['total_districts']
        if count > 0:
            for key in ['avg_potential', 'avg_rent_quota', 'avg_children_quota']:
                stats[key] /= count
    
    # Sortiere die Daten nach verschiedenen Kriterien
    top_potential = sorted(analyzed_data, key=lambda x: x['potential_score'], reverse=True)
    top_households = sorted(analyzed_data, key=lambda x: x['Haushalte'] or 0, reverse=True)
    
    return render_template('route_analysis.html',
                         areas=areas,
                         top_potential=top_potential[:10],
                         top_households=top_households[:10],
                         total_data=analyzed_data)

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

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001) 