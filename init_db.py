from app import app, db, User, Route, Volunteer, RouteRegistration
from migrations.add_meeting_point import upgrade as upgrade_meeting_point
from migrations.add_max_volunteers import upgrade as upgrade_max_volunteers
import json
from datetime import datetime
import os

def backup_data():
    """Erstellt ein Backup der wichtigen Daten"""
    with app.app_context():
        try:
            backup = {
                'routes': [],
                'volunteers': [],
                'registrations': []
            }
            
            # Backup Routen
            routes = Route.query.all()
            for route in routes:
                route_data = {
                    'city': route.city,
                    'street': route.street,
                    'house_numbers': route.house_numbers,
                    'zip_code': route.zip_code,
                    'mobilization_index': route.mobilization_index,
                    'conviction_index': route.conviction_index,
                    'households': route.households,
                    'rental_percentage': route.rental_percentage,
                    'lat': route.lat,
                    'lon': route.lon,
                    'meeting_point': route.meeting_point,
                    'meeting_point_lat': route.meeting_point_lat,
                    'meeting_point_lon': route.meeting_point_lon,
                    'max_volunteers': route.max_volunteers,
                    'is_active': route.is_active,
                    'needs_review': route.needs_review
                }
                backup['routes'].append(route_data)
            
            # Backup Freiwillige
            volunteers = Volunteer.query.all()
            for volunteer in volunteers:
                volunteer_data = {
                    'name': volunteer.name,
                    'email': volunteer.email,
                    'phone': volunteer.phone
                }
                backup['volunteers'].append(volunteer_data)
            
            # Backup Registrierungen
            registrations = RouteRegistration.query.all()
            for reg in registrations:
                reg_data = {
                    'volunteer_email': reg.volunteer.email,  # Referenz über E-Mail
                    'route_identifier': f"{reg.route.street}_{reg.route.house_numbers}",  # Eindeutige Route-ID
                    'date': reg.date.strftime('%Y-%m-%d'),
                    'time_slot': reg.time_slot,
                    'status': reg.status
                }
                backup['registrations'].append(reg_data)
            
            # Speichere Backup
            backup_file = 'data_backup.json'
            with open(backup_file, 'w') as f:
                json.dump(backup, f, indent=2)
            print(f"Backup erstellt: {len(backup['routes'])} Routen, {len(backup['volunteers'])} Freiwillige, {len(backup['registrations'])} Registrierungen")
            
        except Exception as e:
            print(f"Fehler beim Backup: {str(e)}")

def restore_data():
    """Stellt Daten aus dem Backup wieder her"""
    backup_file = 'data_backup.json'
    if not os.path.exists(backup_file):
        print("Kein Backup gefunden")
        return
    
    with app.app_context():
        try:
            with open(backup_file, 'r') as f:
                backup = json.load(f)
            
            # Stelle Routen wieder her
            for route_data in backup['routes']:
                existing_route = Route.query.filter_by(
                    street=route_data['street'],
                    house_numbers=route_data['house_numbers']
                ).first()
                
                if not existing_route:
                    route = Route(**route_data)
                    db.session.add(route)
            
            # Stelle Freiwillige wieder her
            for volunteer_data in backup['volunteers']:
                existing_volunteer = Volunteer.query.filter_by(
                    email=volunteer_data['email']
                ).first()
                
                if not existing_volunteer:
                    volunteer = Volunteer(**volunteer_data)
                    db.session.add(volunteer)
            
            # Stelle Registrierungen wieder her
            for reg_data in backup['registrations']:
                # Finde zugehörigen Freiwilligen und Route
                volunteer = Volunteer.query.filter_by(email=reg_data['volunteer_email']).first()
                street, house_numbers = reg_data['route_identifier'].split('_')
                route = Route.query.filter_by(street=street, house_numbers=house_numbers).first()
                
                if volunteer and route:
                    existing_registration = RouteRegistration.query.filter_by(
                        volunteer_id=volunteer.id,
                        route_id=route.id,
                        date=datetime.strptime(reg_data['date'], '%Y-%m-%d').date(),
                        time_slot=reg_data['time_slot']
                    ).first()
                    
                    if not existing_registration:
                        registration = RouteRegistration(
                            volunteer_id=volunteer.id,
                            route_id=route.id,
                            date=datetime.strptime(reg_data['date'], '%Y-%m-%d').date(),
                            time_slot=reg_data['time_slot'],
                            status=reg_data['status']
                        )
                        db.session.add(registration)
            
            db.session.commit()
            print("Backup erfolgreich wiederhergestellt")
            
        except Exception as e:
            db.session.rollback()
            print(f"Fehler bei der Wiederherstellung: {str(e)}")

def init_db():
    with app.app_context():
        print("Versuche Backup wiederherzustellen...")
        restore_data()
        
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
        
        # Erstelle Backup der aktuellen Daten
        print("Erstelle Backup...")
        backup_data()

def add_routes():
    with app.app_context():
        routes_data = [
            # Neue Routen um Südwall 38, Krefeld
            {
                'street': 'Südwall',
                'house_numbers': '30-50',
                'zip_code': '47798',
                'city': 'Krefeld',
                'lat': 51.3325,
                'lon': 6.5645,
                'mobilization_index': 2.8,
                'conviction_index': 2.7,
                'households': 48,
                'rental_percentage': 73.5,
                'meeting_point': 'Vor dem Südwall 38',
                'meeting_point_lat': 51.3325,
                'meeting_point_lon': 6.5645,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Neue Linner Straße',
                'house_numbers': '60-110',
                'zip_code': '47798',
                'city': 'Krefeld',
                'lat': 51.3328,
                'lon': 6.5648,
                'mobilization_index': 2.9,
                'conviction_index': 2.8,
                'households': 52,
                'rental_percentage': 71.2,
                'meeting_point': 'Ecke Neue Linner Straße/Südwall',
                'meeting_point_lat': 51.3328,
                'meeting_point_lon': 6.5648,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Petersstraße',
                'house_numbers': '1-45',
                'zip_code': '47798',
                'city': 'Krefeld',
                'lat': 51.3322,
                'lon': 6.5642,
                'mobilization_index': 2.7,
                'conviction_index': 2.9,
                'households': 45,
                'rental_percentage': 74.8,
                'meeting_point': 'Vor der Petersstraße 1',
                'meeting_point_lat': 51.3322,
                'meeting_point_lon': 6.5642,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Dreikönigenstraße',
                'house_numbers': '20-70',
                'zip_code': '47798',
                'city': 'Krefeld',
                'lat': 51.3320,
                'lon': 6.5640,
                'mobilization_index': 3.0,
                'conviction_index': 2.8,
                'households': 55,
                'rental_percentage': 72.5,
                'meeting_point': 'Am Dreikönigenplatz',
                'meeting_point_lat': 51.3320,
                'meeting_point_lon': 6.5640,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Stephanstraße',
                'house_numbers': '10-60',
                'zip_code': '47798',
                'city': 'Krefeld',
                'lat': 51.3330,
                'lon': 6.5650,
                'mobilization_index': 2.8,
                'conviction_index': 2.6,
                'households': 50,
                'rental_percentage': 73.8,
                'meeting_point': 'Vor der Stephanstraße 30',
                'meeting_point_lat': 51.3330,
                'meeting_point_lon': 6.5650,
                'is_active': False,
                'needs_review': True
            },
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
            },
            # Neue Routen um Roosenstraße 7a, Neukirchen-Vluyn
            {
                'street': 'Roosenstraße',
                'house_numbers': '1-15',
                'zip_code': '47506',
                'city': 'Neukirchen-Vluyn',
                'lat': 51.4482,
                'lon': 6.5452,
                'mobilization_index': 2.8,
                'conviction_index': 2.7,
                'households': 42,
                'rental_percentage': 65.5,
                'meeting_point': 'Vor der Roosenstraße 7a',
                'meeting_point_lat': 51.4482,
                'meeting_point_lon': 6.5452,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Hochstraße',
                'house_numbers': '50-100',
                'zip_code': '47506',
                'city': 'Neukirchen-Vluyn',
                'lat': 51.4485,
                'lon': 6.5455,
                'mobilization_index': 2.6,
                'conviction_index': 2.8,
                'households': 48,
                'rental_percentage': 68.3,
                'meeting_point': 'Ecke Hochstraße/Roosenstraße',
                'meeting_point_lat': 51.4485,
                'meeting_point_lon': 6.5455,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Niederrheinallee',
                'house_numbers': '100-160',
                'zip_code': '47506',
                'city': 'Neukirchen-Vluyn',
                'lat': 51.4478,
                'lon': 6.5448,
                'mobilization_index': 2.9,
                'conviction_index': 2.6,
                'households': 52,
                'rental_percentage': 70.2,
                'meeting_point': 'Vor dem Einkaufszentrum Niederrheinallee',
                'meeting_point_lat': 51.4478,
                'meeting_point_lon': 6.5448,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Ernst-Moritz-Arndt-Straße',
                'house_numbers': '20-80',
                'zip_code': '47506',
                'city': 'Neukirchen-Vluyn',
                'lat': 51.4488,
                'lon': 6.5445,
                'mobilization_index': 2.7,
                'conviction_index': 2.9,
                'households': 45,
                'rental_percentage': 67.8,
                'meeting_point': 'Am Parkplatz Ernst-Moritz-Arndt-Straße',
                'meeting_point_lat': 51.4488,
                'meeting_point_lon': 6.5445,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Andreas-Bräm-Straße',
                'house_numbers': '1-55',
                'zip_code': '47506',
                'city': 'Neukirchen-Vluyn',
                'lat': 51.4475,
                'lon': 6.5458,
                'mobilization_index': 2.8,
                'conviction_index': 2.7,
                'households': 50,
                'rental_percentage': 69.5,
                'meeting_point': 'Vor der Grundschule',
                'meeting_point_lat': 51.4475,
                'meeting_point_lon': 6.5458,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Mozartstraße',
                'house_numbers': '10-70',
                'zip_code': '47506',
                'city': 'Neukirchen-Vluyn',
                'lat': 51.4492,
                'lon': 6.5462,
                'mobilization_index': 2.5,
                'conviction_index': 2.8,
                'households': 55,
                'rental_percentage': 66.8,
                'meeting_point': 'Vor dem Musikschulgebäude',
                'meeting_point_lat': 51.4492,
                'meeting_point_lon': 6.5462,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Goethestraße',
                'house_numbers': '15-85',
                'zip_code': '47506',
                'city': 'Neukirchen-Vluyn',
                'lat': 51.4495,
                'lon': 6.5450,
                'mobilization_index': 3.0,
                'conviction_index': 2.8,
                'households': 58,
                'rental_percentage': 71.2,
                'meeting_point': 'Am Goetheplatz',
                'meeting_point_lat': 51.4495,
                'meeting_point_lon': 6.5450,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Lindenstraße',
                'house_numbers': '30-90',
                'zip_code': '47506',
                'city': 'Neukirchen-Vluyn',
                'lat': 51.4498,
                'lon': 6.5465,
                'mobilization_index': 2.8,
                'conviction_index': 2.6,
                'households': 52,
                'rental_percentage': 68.5,
                'meeting_point': 'Vor dem Linden-Café',
                'meeting_point_lat': 51.4498,
                'meeting_point_lon': 6.5465,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Schulstraße',
                'house_numbers': '5-65',
                'zip_code': '47506',
                'city': 'Neukirchen-Vluyn',
                'lat': 51.4472,
                'lon': 6.5468,
                'mobilization_index': 2.9,
                'conviction_index': 2.7,
                'households': 60,
                'rental_percentage': 70.8,
                'meeting_point': 'Vor der Julius-Stursberg-Schule',
                'meeting_point_lat': 51.4472,
                'meeting_point_lon': 6.5468,
                'is_active': False,
                'needs_review': True
            },
            {
                'street': 'Poststraße',
                'house_numbers': '20-80',
                'zip_code': '47506',
                'city': 'Neukirchen-Vluyn',
                'lat': 51.4468,
                'lon': 6.5455,
                'mobilization_index': 2.7,
                'conviction_index': 2.8,
                'households': 54,
                'rental_percentage': 67.9,
                'meeting_point': 'Vor dem alten Postamt',
                'meeting_point_lat': 51.4468,
                'meeting_point_lon': 6.5455,
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