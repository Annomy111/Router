from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Route(db.Model):
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
    meeting_point = db.Column(db.String(500))  # Neues Feld für den Treffpunkt
    meeting_point_lat = db.Column(db.Float)    # Koordinaten des Treffpunkts
    meeting_point_lon = db.Column(db.Float)    # Koordinaten des Treffpunkts
    registrations = db.relationship('RouteRegistration', backref='route', lazy=True)
    max_volunteers = db.Column(db.Integer, default=4)  # Maximale Anzahl der Freiwilligen

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
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    registrations = db.relationship('RouteRegistration', backref='volunteer', lazy=True)

class RouteRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    volunteer_id = db.Column(db.Integer, db.ForeignKey('volunteer.id'), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('route.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 