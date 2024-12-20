from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    registrations = db.relationship('RouteRegistration', backref='route', lazy=True)
    max_volunteers = db.Column(db.Integer, default=4)
    is_active = db.Column(db.Boolean, default=True)

    def get_registration_stats(self):
        """Berechnet Statistiken für die Routenregistrierungen"""
        active_registrations = len([r for r in self.registrations if r.status != 'abgesagt'])
        return {
            'current': active_registrations,
            'maximum': self.max_volunteers,
            'percentage': (active_registrations / self.max_volunteers) * 100 if self.max_volunteers > 0 else 0,
            'available_slots': max(0, self.max_volunteers - active_registrations)
        }

class Volunteer(db.Model):
    __tablename__ = 'volunteer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    registrations = db.relationship('RouteRegistration', backref='volunteer', lazy=True)

class RouteRegistration(db.Model):
    __tablename__ = 'route_registration'
    id = db.Column(db.Integer, primary_key=True)
    volunteer_id = db.Column(db.Integer, db.ForeignKey('volunteer.id'), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('route.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='geplant')  # geplant, abgeschlossen, abgesagt

class WohnquartierAnalyse(db.Model):
    __tablename__ = 'wohnquartier'
    
    id = db.Column(db.Integer, primary_key=True)
    Gemeinde = db.Column(db.String(100))
    Haushalte = db.Column(db.Integer)
    Haushalte_zur_Miete = db.Column(db.Float)
    Haushalte_mit_Kindern = db.Column(db.Float)
    
    # Wahlkreis- und Quartiersdetails
    WKR_SCHLUESSEL = db.Column(db.String(50))
    WKR_NAME = db.Column(db.String(100))
    WOHNQUART_SCHLUESSEL = db.Column(db.String(50))
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
        
        # Gewichteter Score
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