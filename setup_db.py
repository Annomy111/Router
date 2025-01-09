from app import app, db
from models import Route, User

def setup_database():
    with app.app_context():
        # Erstelle Tabellen
        db.create_all()
        print("Tabellen wurden erstellt")
        
        # Erstelle Admin-Benutzer
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin-Benutzer wurde erstellt")
        
        # Füge eine Test-Route hinzu
        if Route.query.count() == 0:
            test_route = Route(
                city="Krefeld",
                street="Teststraße",
                house_numbers="1-10",
                district="Test",
                zip_code="47798",
                mobilization_index=3,
                conviction_index=3,
                households=50,
                rental_percentage=75.0,
                lat=51.333,
                lon=6.564,
                meeting_point="Testpunkt",
                is_active=True
            )
            db.session.add(test_route)
            db.session.commit()
            print("Test-Route wurde hinzugefügt")
        
        print("Datenbank-Setup abgeschlossen")

if __name__ == '__main__':
    setup_database()