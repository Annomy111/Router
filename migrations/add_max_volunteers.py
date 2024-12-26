from flask import current_app
from models import db, Route
from sqlalchemy import text

def upgrade():
    with current_app.app_context():
        with db.engine.connect() as conn:
            conn.execute(text('''
                ALTER TABLE route 
                ADD COLUMN IF NOT EXISTS max_volunteers INTEGER DEFAULT 2
            '''))
            conn.commit()
        
        # Setze Standardwerte für bestehende Routen
        routes = Route.query.all()
        for route in routes:
            if route.max_volunteers is None:
                route.max_volunteers = 2
        
        db.session.commit()

def downgrade():
    with current_app.app_context():
        with db.engine.connect() as conn:
            conn.execute(text('''
                ALTER TABLE route 
                DROP COLUMN IF EXISTS max_volunteers
            '''))
            conn.commit()

if __name__ == '__main__':
    try:
        upgrade()
    except Exception as e:
        print(f"× Fehler bei der Migration: {str(e)}")