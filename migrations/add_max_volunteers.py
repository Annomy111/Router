from app import app, db
from models import Route

def upgrade():
    """Fügt das max_volunteers Feld zur Route-Tabelle hinzu"""
    with app.app_context():
        try:
            # Füge neue Spalte hinzu
            db.engine.execute('ALTER TABLE route ADD COLUMN max_volunteers INTEGER DEFAULT 4')
            
            # Aktualisiere bestehende Routen
            routes = Route.query.all()
            for route in routes:
                route.max_volunteers = 4
            
            db.session.commit()
            print("✓ Max Volunteers Migration erfolgreich")
        except Exception as e:
            db.session.rollback()
            print(f"× Fehler bei der Migration: {str(e)}")

def downgrade():
    """Entfernt das max_volunteers Feld von der Route-Tabelle"""
    with app.app_context():
        try:
            db.engine.execute('ALTER TABLE route DROP COLUMN max_volunteers')
            db.session.commit()
            print("✓ Max Volunteers Downgrade erfolgreich")
        except Exception as e:
            db.session.rollback()
            print(f"× Fehler beim Downgrade: {str(e)}")

if __name__ == '__main__':
    upgrade()