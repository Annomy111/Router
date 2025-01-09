import os
from dotenv import load_dotenv
from supabase import create_client
from app import app, db, Route, Volunteer, RouteRegistration, User
import json
import traceback

# Lade Umgebungsvariablen
load_dotenv()

# Initialisiere Supabase Client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_ANON_KEY')
)

def migrate_data():
    try:
        print("Starte Migration nach Supabase...")
        
        with app.app_context():
            # Migriere Routen
            print("\nMigriere Routen...")
            routes = Route.query.all()
            for route in routes:
                try:
                    route_data = {
                        'id': route.id,
                        'city': route.city,
                        'street': route.street,
                        'house_numbers': route.house_numbers,
                        'zip_code': route.zip_code,
                        'district': route.district,
                        'mobilization_index': route.mobilization_index,
                        'conviction_index': route.conviction_index,
                        'households': route.households,
                        'rental_percentage': float(route.rental_percentage) if route.rental_percentage else None,
                        'lat': float(route.lat) if route.lat else None,
                        'lon': float(route.lon) if route.lon else None,
                        'meeting_point': route.meeting_point,
                        'meeting_point_lat': float(route.meeting_point_lat) if route.meeting_point_lat else None,
                        'meeting_point_lon': float(route.meeting_point_lon) if route.meeting_point_lon else None,
                        'max_volunteers': route.max_volunteers,
                        'is_active': route.is_active,
                        'path_coordinates': route.path_coordinates,
                        'needs_review': route.needs_review
                    }
                    result = supabase.table('routes').upsert(route_data).execute()
                    print(f"Route {route.id} ({route.street}) erfolgreich migriert")
                except Exception as e:
                    print(f"Fehler bei Route {route.id}: {str(e)}")
                    print(traceback.format_exc())
                    continue
            print(f"{len(routes)} Routen migriert")

            # Migriere Freiwillige
            print("\nMigriere Freiwillige...")
            volunteers = Volunteer.query.all()
            for volunteer in volunteers:
                try:
                    volunteer_data = {
                        'id': volunteer.id,
                        'name': volunteer.name,
                        'email': volunteer.email,
                        'phone': volunteer.phone
                    }
                    result = supabase.table('volunteers').upsert(volunteer_data).execute()
                    print(f"Freiwilliger {volunteer.id} ({volunteer.name}) erfolgreich migriert")
                except Exception as e:
                    print(f"Fehler bei Freiwilligem {volunteer.id}: {str(e)}")
                    print(traceback.format_exc())
                    continue
            print(f"{len(volunteers)} Freiwillige migriert")

            # Migriere Routenregistrierungen
            print("\nMigriere Routenregistrierungen...")
            registrations = RouteRegistration.query.all()
            for registration in registrations:
                try:
                    registration_data = {
                        'id': registration.id,
                        'volunteer_id': registration.volunteer_id,
                        'route_id': registration.route_id,
                        'date': registration.date.isoformat(),
                        'time_slot': registration.time_slot,
                        'status': registration.status
                    }
                    result = supabase.table('route_registrations').upsert(registration_data).execute()
                    print(f"Registrierung {registration.id} erfolgreich migriert")
                except Exception as e:
                    print(f"Fehler bei Registrierung {registration.id}: {str(e)}")
                    print(traceback.format_exc())
                    continue
            print(f"{len(registrations)} Registrierungen migriert")

            # Migriere Benutzer
            print("\nMigriere Benutzer...")
            users = User.query.all()
            for user in users:
                try:
                    user_data = {
                        'id': user.id,
                        'username': user.username,
                        'password_hash': user.password_hash,
                        'is_admin': user.is_admin
                    }
                    result = supabase.table('users').upsert(user_data).execute()
                    print(f"Benutzer {user.id} ({user.username}) erfolgreich migriert")
                except Exception as e:
                    print(f"Fehler bei Benutzer {user.id}: {str(e)}")
                    print(traceback.format_exc())
                    continue
            print(f"{len(users)} Benutzer migriert")

        print("\nMigration erfolgreich abgeschlossen!")
        return True

    except Exception as e:
        print(f"\nFehler bei der Migration: {str(e)}")
        print(traceback.format_exc())
        return False

if __name__ == '__main__':
    migrate_data() 