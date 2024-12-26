from app import app, db, User, Route
from migrations.add_meeting_point import upgrade as upgrade_meeting_point
from migrations.add_max_volunteers import upgrade as upgrade_max_volunteers

def init_db():
    with app.app_context():
        # Erstelle alle Tabellen
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
        
        # Füge neue Routen um Südwall 38 hinzu
        add_routes()
        
        print("Datenbankinitialisierung abgeschlossen")

def add_routes():
    with app.app_context():
        routes_data = [
            # Neue Routen um Südwall 38, Krefeld
            {
                'street': 'Südwall',
                'house_numbers': '36-40',
                'zip_code': '47798',
                'city': 'Krefeld',
                'lat': 51.3324,
                'lon': 6.5643,
                'mobilization_index': 2.8,
                'conviction_index': 2.5,
                'households': 25,
                'rental_percentage': 75.5,
                'meeting_point': 'Vor dem Café am Südwall 38',
                'meeting_point_lat': 51.3324,
                'meeting_point_lon': 6.5643,
                'is_active': False,  # Nicht aktiv bis zum Review
                'needs_review': True
            },
            {
                'street': 'Friedrichstraße',
                'house_numbers': '1-15',
                'zip_code': '47798',
                'city': 'Krefeld',
                'lat': 51.3326,
                'lon': 6.5648,
                'mobilization_index': 2.6,
                'conviction_index': 2.7,
                'households': 30,
                'rental_percentage': 68.3,
                'meeting_point': 'Ecke Friedrichstraße/Südwall',
                'meeting_point_lat': 51.3326,
                'meeting_point_lon': 6.5648,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Petersstraße',
                'house_numbers': '2-20',
                'zip_code': '47798',
                'city': 'Krefeld',
                'lat': 51.3322,
                'lon': 6.5638,
                'mobilization_index': 2.4,
                'conviction_index': 2.6,
                'households': 28,
                'rental_percentage': 72.1,
                'meeting_point': 'Vor der Peterskirche',
                'meeting_point_lat': 51.3322,
                'meeting_point_lon': 6.5638,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Neue Linner Straße',
                'house_numbers': '1-19',
                'zip_code': '47798',
                'city': 'Krefeld',
                'lat': 51.3328,
                'lon': 6.5650,
                'mobilization_index': 2.9,
                'conviction_index': 2.8,
                'households': 35,
                'rental_percentage': 70.8,
                'meeting_point': 'Ecke Neue Linner Straße/Südwall',
                'meeting_point_lat': 51.3328,
                'meeting_point_lon': 6.5650,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Stephanstraße',
                'house_numbers': '1-17',
                'zip_code': '47798',
                'city': 'Krefeld',
                'lat': 51.3320,
                'lon': 6.5635,
                'mobilization_index': 2.5,
                'conviction_index': 2.4,
                'households': 22,
                'rental_percentage': 65.4,
                'meeting_point': 'Vor dem Stadthaus',
                'meeting_point_lat': 51.3320,
                'meeting_point_lon': 6.5635,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Königstraße',
                'house_numbers': '2-22',
                'zip_code': '47798',
                'city': 'Krefeld',
                'lat': 51.3330,
                'lon': 6.5645,
                'mobilization_index': 3.0,
                'conviction_index': 2.9,
                'households': 40,
                'rental_percentage': 73.2,
                'meeting_point': 'Vor dem Königshof',
                'meeting_point_lat': 51.3330,
                'meeting_point_lon': 6.5645,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Dreikönigenstraße',
                'house_numbers': '1-21',
                'zip_code': '47798',
                'city': 'Krefeld',
                'lat': 51.3325,
                'lon': 6.5640,
                'mobilization_index': 2.7,
                'conviction_index': 2.6,
                'households': 32,
                'rental_percentage': 69.7,
                'meeting_point': 'Ecke Dreikönigenstraße/Südwall',
                'meeting_point_lat': 51.3325,
                'meeting_point_lon': 6.5640,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Rheinstraße',
                'house_numbers': '2-24',
                'zip_code': '47798',
                'city': 'Krefeld',
                'lat': 51.3327,
                'lon': 6.5647,
                'mobilization_index': 2.8,
                'conviction_index': 2.7,
                'households': 38,
                'rental_percentage': 71.5,
                'meeting_point': 'Vor dem Stadttheater',
                'meeting_point_lat': 51.3327,
                'meeting_point_lon': 6.5647,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Marktstraße',
                'house_numbers': '1-19',
                'zip_code': '47798',
                'city': 'Krefeld',
                'lat': 51.3323,
                'lon': 6.5642,
                'mobilization_index': 2.6,
                'conviction_index': 2.5,
                'households': 28,
                'rental_percentage': 67.8,
                'meeting_point': 'Am alten Markt',
                'meeting_point_lat': 51.3323,
                'meeting_point_lon': 6.5642,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'St.-Anton-Straße',
                'house_numbers': '2-18',
                'zip_code': '47798',
                'city': 'Krefeld',
                'lat': 51.3321,
                'lon': 6.5637,
                'mobilization_index': 2.5,
                'conviction_index': 2.4,
                'households': 25,
                'rental_percentage': 66.9,
                'meeting_point': 'Vor der St. Anton Kirche',
                'meeting_point_lat': 51.3321,
                'meeting_point_lon': 6.5637,
                'is_active': False,
                'needs_review': True
            }
        ]

        for route_data in routes_data:
            # Prüfe, ob die Route bereits existiert
            existing_route = Route.query.filter_by(
                street=route_data['street'],
                house_numbers=route_data['house_numbers']
            ).first()
            
            if not existing_route:
                # Erstelle ein neues Route-Objekt
                route = Route(**route_data)
                db.session.add(route)
                print(f"Neue Route hinzugefügt: {route_data['street']} {route_data['house_numbers']}")
        
        db.session.commit()
        print("Neue Routen wurden erfolgreich hinzugefügt")

if __name__ == '__main__':
    init_db()

# Führe Migrationen aus
with app.app_context():
    try:
        upgrade_meeting_point()
        print("✓ Meeting Point Migration erfolgreich")
    except Exception as e:
        print(f"× Meeting Point Migration fehlgeschlagen: {str(e)}")
    
    try:
        upgrade_max_volunteers()
        print("✓ Max Volunteers Migration erfolgreich")
    except Exception as e:
        print(f"× Max Volunteers Migration fehlgeschlagen: {str(e)}")

print("Datenbankinitialisierung abgeschlossen") 