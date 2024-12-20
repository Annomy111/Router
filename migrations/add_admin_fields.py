from app import app, db, User, Route
from werkzeug.security import generate_password_hash
from sqlalchemy import text

def upgrade():
    with app.app_context():
        # Füge is_active zu Route hinzu
        db.session.execute(text('ALTER TABLE route ADD COLUMN is_active BOOLEAN DEFAULT TRUE'))
        
        # Erstelle User-Tabelle
        db.session.execute(text('''
            CREATE TABLE user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(120) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE
            )
        '''))
        
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

if __name__ == '__main__':
    upgrade() 