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

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dein-geheimer-schluessel')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///neue_daten.db'
app.config['MAPBOX_TOKEN'] = os.environ.get('MAPBOX_TOKEN', 'pk.eyJ1Ijoid2luemVuZHd5ZXJzIiwiYSI6ImNscmx3Z2FtaTBkOHYya3BpbmxnOWFxbXIifQ.qHvhs6vhn6ggAXMg8TA_8g')

# E-Mail-Konfiguration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
app.config['ADMIN_EMAIL'] = 'Fedo.Hagge-Kubat@fu-berlin.de'

if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)

db = SQLAlchemy(app)
mail = Mail(app)

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
    routes = Route.query.all()
    return render_template('index.html', routes=routes)

@app.route('/karte')
def map_view():
    routes = Route.query.all()
    
    # Erstelle Karte zentriert auf Moers
    m = folium.Map(location=[51.451, 6.626], zoom_start=11)
    
    # Füge Cluster-Marker-Gruppe hinzu
    marker_cluster = plugins.MarkerCluster(name="Routen")
    m.add_child(marker_cluster)
    
    # Füge Layer Control hinzu
    folium.LayerControl().add_to(m)
    
    # Erstelle Farbskala für Potenzial
    def get_color(mobilization, conviction):
        avg = (mobilization + conviction) / 2
        if avg >= 2.5:
            return 'darkred'
        elif avg >= 2:
            return 'red'
        elif avg >= 1.5:
            return 'orange'
        else:
            return 'lightred'
    
    # Füge Marker für jede Route hinzu
    for route in routes:
        # Erstelle detaillierten Popup-Inhalt
        popup_html = f"""
        <div style="min-width: 200px;">
            <h4 style="color: #E3000F; margin-bottom: 10px;">{route.street} {route.house_numbers}</h4>
            <p style="margin-bottom: 5px;"><strong>Stadt:</strong> {route.city}</p>
            <div style="margin: 10px 0;">
                <div style="margin-bottom: 5px;">
                    <strong>Mobilisierung:</strong> {route.mobilization_index}/3
                    <div class="progress" style="height: 10px; background-color: #f5f5f5; border-radius: 5px;">
                        <div class="progress-bar" style="width: {(route.mobilization_index/3*100)}%; 
                             background-color: #E3000F; border-radius: 5px;"></div>
                    </div>
                </div>
                <div style="margin-bottom: 5px;">
                    <strong>Überzeugung:</strong> {route.conviction_index}/3
                    <div class="progress" style="height: 10px; background-color: #f5f5f5; border-radius: 5px;">
                        <div class="progress-bar" style="width: {(route.conviction_index/3*100)}%; 
                             background-color: #E3000F; border-radius: 5px;"></div>
                    </div>
                </div>
            </div>
        """
        
        if route.households:
            popup_html += f"<p><strong>Haushalte:</strong> {route.households}</p>"
        if route.rental_percentage:
            popup_html += f"<p><strong>Mietquote:</strong> {route.rental_percentage:.1f}%</p>"
            
        popup_html += f"""
            <div style="margin-top: 10px;">
                <a href="/route/{route.id}" 
                   style="background-color: #E3000F; color: white; 
                          padding: 5px 10px; text-decoration: none; 
                          border-radius: 5px; display: inline-block;">
                    Details ansehen
                </a>
            </div>
        </div>
        """
        
        # Erstelle Icon mit dynamischer Farbe
        icon = folium.Icon(
            color=get_color(route.mobilization_index, route.conviction_index),
            icon='info-sign'
        )
        
        # Füge Marker zum Cluster hinzu
        folium.Marker(
            [route.lat, route.lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{route.street} ({route.city})",
            icon=icon
        ).add_to(marker_cluster)
        
        # Füge einen Kreis hinzu, um den Einzugsbereich zu visualisieren
        folium.Circle(
            [route.lat, route.lon],
            radius=200,  # Radius in Metern
            color="#E3000F",
            fill=True,
            fillColor="#E3000F",
            fillOpacity=0.1
        ).add_to(m)
    
    # Füge Legende hinzu
    legend_html = """
    <div style="position: fixed; bottom: 50px; right: 50px; z-index: 1000; background-color: white;
                padding: 10px; border: 2px solid #E3000F; border-radius: 5px;">
        <h4 style="color: #E3000F; margin-bottom: 10px;">Legende</h4>
        <p><i class="fa fa-circle" style="color: darkred;"></i> Sehr hohes Potenzial (≥2.5)</p>
        <p><i class="fa fa-circle" style="color: red;"></i> Hohes Potenzial (≥2.0)</p>
        <p><i class="fa fa-circle" style="color: orange;"></i> Mittleres Potenzial (≥1.5)</p>
        <p><i class="fa fa-circle" style="color: lightred;"></i> Normales Potenzial (<1.5)</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
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
        
        route = Route.query.get(route_id)
        
        # Erstelle neue Routenregistrierung
        registration = RouteRegistration(
            volunteer_id=volunteer.id,
            route_id=route_id,
            date=datetime.strptime(date, '%Y-%m-%d'),
            time_slot=time_slot
        )
        db.session.add(registration)
        db.session.commit()
        
        # Sende E-Mail-Benachrichtigung
        send_registration_notification(volunteer, route, registration)
        
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
    try:
        # Hole alle Wohnquartiere
        wohnquartiere = WohnquartierAnalyse.query.all()
        analyzed_data = []
        
        # Gruppiere die Daten nach Gemeinde
        gemeinde_data = {}
        for wq in wohnquartiere:
            if not wq.Gemeinde:  # Überspringe Einträge ohne Gemeinde
                continue
                
            if wq.Gemeinde not in gemeinde_data:
                gemeinde_data[wq.Gemeinde] = {
                    'Haushalte': 0,
                    'Haushalte_zur_Miete': 0,
                    'Haushalte_mit_Kindern': 0,
                    'Mobilisierung_Sum': 0,
                    'Ueberzeugung_Sum': 0,
                    'Anzahl': 0
                }
            
            gd = gemeinde_data[wq.Gemeinde]
            gd['Haushalte'] += wq.Haushalte or 0
            gd['Haushalte_zur_Miete'] += wq.Haushalte_zur_Miete or 0
            gd['Haushalte_mit_Kindern'] += wq.Haushalte_mit_Kindern or 0
            gd['Mobilisierung_Sum'] += wq.MOBILISIERUNGSINDEX_KLASSE_WKR or 0
            gd['Ueberzeugung_Sum'] += wq.UEBERZEUGUNSINDEX_KLASSE_WKR or 0
            gd['Anzahl'] += 1
            
            # Berechne Scores für einzelnes Wohnquartier
            if wq.Haushalte and wq.Haushalte > 0:
                mietquote = (wq.Haushalte_zur_Miete or 0) / wq.Haushalte * 100
                kinderquote = (wq.Haushalte_mit_Kindern or 0) / wq.Haushalte * 100
                mobilisierung = wq.MOBILISIERUNGSINDEX_KLASSE_WKR or 0
                ueberzeugung = wq.UEBERZEUGUNSINDEX_KLASSE_WKR or 0
                
                potential_score = (
                    (mietquote / 100 * 0.3) +  # Mietquote (30%)
                    (kinderquote / 100 * 0.2) +  # Kinderquote (20%)
                    (mobilisierung / 3 * 0.25) +  # Mobilisierung (25%)
                    (ueberzeugung / 3 * 0.25)  # Überzeugung (25%)
                ) * 3  # Skalierung auf 0-3
                
                analyzed_data.append({
                    'Gemeinde': wq.Gemeinde,
                    'Haushalte': wq.Haushalte,
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
                        'total_districts': gd['Anzahl']
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

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001) 