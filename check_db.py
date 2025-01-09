from app import app, db
from models import Route
import os

def check_database():
    with app.app_context():
        try:
            print("Datenbankverbindungs-URL:", app.config['SQLALCHEMY_DATABASE_URI'])
            print("Versuche Verbindung zur Datenbank...")
            
            # Test der Datenbankverbindung
            db.engine.connect()
            print("Datenbankverbindung erfolgreich hergestellt!")
            
            route_count = Route.query.count()
            print(f"Anzahl Routen: {route_count}")
            
            if route_count == 0:
                print("Keine Routen in der Datenbank gefunden")
            else:
                routes = Route.query.all()
                print("\nVerfügbare Routen:")
                for route in routes:
                    print(f"- {route.city}: {route.street} {route.house_numbers}")
                    
        except Exception as e:
            print(f"Fehler bei der Datenbankverbindung: {str(e)}")
            print("\nUmgebungsvariablen:")
            print("SUPABASE_DATABASE_URL:", os.getenv('SUPABASE_DATABASE_URL'))

if __name__ == '__main__':
    check_database() 