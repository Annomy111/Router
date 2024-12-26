from flask import current_app
from models import db, Route
from sqlalchemy import text

def upgrade():
    # Füge neue Spalten hinzu
    with current_app.app_context():
        with db.engine.connect() as conn:
            conn.execute(text('''
                ALTER TABLE route 
                ADD COLUMN IF NOT EXISTS meeting_point VARCHAR(500),
                ADD COLUMN IF NOT EXISTS meeting_point_lat FLOAT,
                ADD COLUMN IF NOT EXISTS meeting_point_lon FLOAT
            '''))
            conn.commit()
        
        # Aktualisiere bestehende Routen mit Treffpunkten
        routes = Route.query.all()
        for route in routes:
            # Setze Standard-Treffpunkt am Anfang der Straße
            house_start = route.house_numbers.split('-')[0]
            route.meeting_point = f"Vor {route.street} {house_start}"
            route.meeting_point_lat = route.lat
            route.meeting_point_lon = route.lon
        
        db.session.commit()

def downgrade():
    # Entferne die Spalten wieder
    with current_app.app_context():
        with db.engine.connect() as conn:
            conn.execute(text('''
                ALTER TABLE route 
                DROP COLUMN IF EXISTS meeting_point,
                DROP COLUMN IF EXISTS meeting_point_lat,
                DROP COLUMN IF EXISTS meeting_point_lon
            '''))
            conn.commit() 