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
            # Neue Routen um Zwickauerstraße 16, Moers
            {
                'street': 'Zwickauerstraße',
                'house_numbers': '2-30',
                'zip_code': '47443',
                'city': 'Moers',
                'lat': 51.4512,
                'lon': 6.6382,
                'mobilization_index': 2.8,
                'conviction_index': 2.6,
                'households': 45,
                'rental_percentage': 72.5,
                'meeting_point': 'Vor der Zwickauerstraße 16',
                'meeting_point_lat': 51.4512,
                'meeting_point_lon': 6.6382,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Essenberger Straße',
                'house_numbers': '100-150',
                'zip_code': '47443',
                'city': 'Moers',
                'lat': 51.4515,
                'lon': 6.6385,
                'mobilization_index': 2.7,
                'conviction_index': 2.5,
                'households': 50,
                'rental_percentage': 68.3,
                'meeting_point': 'Ecke Essenberger Straße/Zwickauerstraße',
                'meeting_point_lat': 51.4515,
                'meeting_point_lon': 6.6385,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Römerstraße',
                'house_numbers': '50-100',
                'zip_code': '47443',
                'city': 'Moers',
                'lat': 51.4508,
                'lon': 6.6378,
                'mobilization_index': 2.9,
                'conviction_index': 2.7,
                'households': 55,
                'rental_percentage': 70.2,
                'meeting_point': 'Vor dem Spielplatz Römerstraße',
                'meeting_point_lat': 51.4508,
                'meeting_point_lon': 6.6378,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Barbarastraße',
                'house_numbers': '1-45',
                'zip_code': '47443',
                'city': 'Moers',
                'lat': 51.4518,
                'lon': 6.6375,
                'mobilization_index': 2.6,
                'conviction_index': 2.8,
                'households': 48,
                'rental_percentage': 71.8,
                'meeting_point': 'Ecke Barbarastraße/Essenberger Straße',
                'meeting_point_lat': 51.4518,
                'meeting_point_lon': 6.6375,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Moselstraße',
                'house_numbers': '20-80',
                'zip_code': '47443',
                'city': 'Moers',
                'lat': 51.4505,
                'lon': 6.6388,
                'mobilization_index': 2.8,
                'conviction_index': 2.6,
                'households': 52,
                'rental_percentage': 69.5,
                'meeting_point': 'Vor dem Kiosk Moselstraße 50',
                'meeting_point_lat': 51.4505,
                'meeting_point_lon': 6.6388,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Kirschenallee',
                'house_numbers': '10-70',
                'zip_code': '47443',
                'city': 'Moers',
                'lat': 51.4522,
                'lon': 6.6392,
                'mobilization_index': 2.7,
                'conviction_index': 2.9,
                'households': 58,
                'rental_percentage': 67.8,
                'meeting_point': 'Am Parkplatz Kirschenallee',
                'meeting_point_lat': 51.4522,
                'meeting_point_lon': 6.6392,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Homberger Straße',
                'house_numbers': '200-260',
                'zip_code': '47443',
                'city': 'Moers',
                'lat': 51.4525,
                'lon': 6.6380,
                'mobilization_index': 3.0,
                'conviction_index': 2.8,
                'households': 62,
                'rental_percentage': 73.2,
                'meeting_point': 'Vor der Bushaltestelle Homberger Straße',
                'meeting_point_lat': 51.4525,
                'meeting_point_lon': 6.6380,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Rheinberger Straße',
                'house_numbers': '150-220',
                'zip_code': '47443',
                'city': 'Moers',
                'lat': 51.4528,
                'lon': 6.6395,
                'mobilization_index': 2.8,
                'conviction_index': 2.7,
                'households': 56,
                'rental_percentage': 70.5,
                'meeting_point': 'Ecke Rheinberger Straße/Homberger Straße',
                'meeting_point_lat': 51.4528,
                'meeting_point_lon': 6.6395,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Duisburger Straße',
                'house_numbers': '300-380',
                'zip_code': '47443',
                'city': 'Moers',
                'lat': 51.4502,
                'lon': 6.6398,
                'mobilization_index': 2.9,
                'conviction_index': 2.6,
                'households': 65,
                'rental_percentage': 72.8,
                'meeting_point': 'Vor dem Supermarkt Duisburger Straße',
                'meeting_point_lat': 51.4502,
                'meeting_point_lon': 6.6398,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Am Jostenhof',
                'house_numbers': '1-55',
                'zip_code': '47443',
                'city': 'Moers',
                'lat': 51.4498,
                'lon': 6.6385,
                'mobilization_index': 2.7,
                'conviction_index': 2.8,
                'households': 54,
                'rental_percentage': 68.9,
                'meeting_point': 'Vor dem Spielplatz Am Jostenhof',
                'meeting_point_lat': 51.4498,
                'meeting_point_lon': 6.6385,
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