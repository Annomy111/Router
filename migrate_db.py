from app import app, db
from migrations.add_meeting_point import upgrade as upgrade_meeting_point
from migrations.add_max_volunteers import upgrade as upgrade_max_volunteers

def run_migrations():
    with app.app_context():
        # Erstelle alle Tabellen
        db.create_all()
        
        try:
            # Führe die Meeting Point Migration aus
            upgrade_meeting_point()
            print("✓ Meeting Point Migration erfolgreich")
        except Exception as e:
            print(f"× Meeting Point Migration fehlgeschlagen: {str(e)}")
        
        try:
            # Führe die Max Volunteers Migration aus
            upgrade_max_volunteers()
            print("✓ Max Volunteers Migration erfolgreich")
        except Exception as e:
            print(f"× Max Volunteers Migration fehlgeschlagen: {str(e)}")

if __name__ == '__main__':
    run_migrations()
    print("Alle Migrationen abgeschlossen!") 