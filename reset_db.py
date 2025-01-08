from app import app, db
from models import Route

def reset_db():
    with app.app_context():
        # Lösche alle existierenden Routen
        Route.query.delete()
        db.session.commit()
        print("✓ Datenbank wurde zurückgesetzt")
        
        # Initialisiere die Datenbank neu
        from app import init_db
        init_db()

if __name__ == '__main__':
    reset_db() 