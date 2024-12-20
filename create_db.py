from app import app, db, User
from models import Route

with app.app_context():
    # Erstelle alle Tabellen
    db.create_all()
    print("Tabellen wurden erstellt")
    
    # Erstelle Admin-Benutzer, wenn noch keiner existiert
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin-Benutzer wurde erstellt")
    else:
        print("Admin-Benutzer existiert bereits")
    
    # Erstelle Beispielrouten, wenn noch keine existieren
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