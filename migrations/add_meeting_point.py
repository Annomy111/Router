from flask import current_app
from models import db, Route
from sqlalchemy import text

def upgrade():
    try:
        db.session.execute(text("""
            ALTER TABLE route ADD COLUMN meeting_point VARCHAR(500);
        """))
    except:
        pass
        
    try:
        db.session.execute(text("""
            ALTER TABLE route ADD COLUMN meeting_point_lat FLOAT;
        """))
    except:
        pass
        
    try:
        db.session.execute(text("""
            ALTER TABLE route ADD COLUMN meeting_point_lon FLOAT;
        """))
    except:
        pass
        
    db.session.commit()
    print("Meeting Point Migration erfolgreich")

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