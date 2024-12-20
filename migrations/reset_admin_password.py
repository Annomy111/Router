from app import app, db, User
from sqlalchemy import text

def reset_password():
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if admin:
            admin.set_password('admin123')
            db.session.commit()
            print("Admin-Passwort wurde zurückgesetzt auf: admin123")
        else:
            print("Admin-Benutzer nicht gefunden!")

if __name__ == '__main__':
    reset_password() 