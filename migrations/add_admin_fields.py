from app import app, db, User, Route
from werkzeug.security import generate_password_hash
from sqlalchemy import text

def upgrade():
    with app.app_context():
        # Erstelle User-Tabelle
        db.session.execute(text('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(120) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE
            )
        '''))
        
        # Prüfe, ob Admin-Benutzer bereits existiert
        result = db.session.execute(text("SELECT * FROM user WHERE username = 'admin'"))
        admin_exists = result.fetchone() is not None
        
        if not admin_exists:
            # Erstelle einen Admin-Benutzer
            admin = User(
                username='admin',
                is_admin=True
            )
            admin.set_password('admin123')  # Ändern Sie dies in ein sicheres Passwort!
            
            db.session.add(admin)
            db.session.commit()
            
            print("Migration erfolgreich durchgeführt")
            print("Admin-Benutzer erstellt:")
            print("Username: admin")
            print("Passwort: admin123")
            print("WICHTIG: Bitte ändern Sie das Passwort nach dem ersten Login!")
        else:
            print("Admin-Benutzer existiert bereits")

if __name__ == '__main__':
    upgrade() 