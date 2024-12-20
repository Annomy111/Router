from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'neue_daten.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

class Route(db.Model):
    __tablename__ = 'route'
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    street = db.Column(db.String(200), nullable=False)
    house_numbers = db.Column(db.String(50), nullable=False)
    mobilization_index = db.Column(db.Integer, nullable=False)
    conviction_index = db.Column(db.Integer, nullable=False)
    households = db.Column(db.Integer)
    rental_percentage = db.Column(db.Float)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    meeting_point = db.Column(db.String(500))
    meeting_point_lat = db.Column(db.Float)
    meeting_point_lon = db.Column(db.Float)
    max_volunteers = db.Column(db.Integer, default=4)
    is_active = db.Column(db.Boolean, default=True)

def setup_db():
    with app.app_context():
        # Erstelle alle Tabellen
        db.create_all()
        print("Tabellen wurden erstellt")
        
        # Erstelle Admin-Benutzer
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin-Benutzer wurde erstellt")
            print("Username: admin")
            print("Passwort: admin123")
        else:
            print("Admin-Benutzer existiert bereits")
        
        # Erstelle Beispielrouten
        if Route.query.count() == 0:
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
            print("Routen wurden erstellt")
        else:
            print("Routen existieren bereits")
        
        print("Datenbankinitialisierung abgeschlossen")

if __name__ == '__main__':
    setup_db() 