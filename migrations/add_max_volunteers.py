from app import app, db

def upgrade():
    with app.app_context():
        with db.engine.connect() as conn:
            conn.execute(db.text("ALTER TABLE route ADD COLUMN max_volunteers INTEGER DEFAULT 2"))
            conn.commit()
            print("Migration erfolgreich: max_volunteers Spalte wurde hinzugefügt")

if __name__ == '__main__':
    try:
        upgrade()
    except Exception as e:
        print(f"× Fehler bei der Migration: {str(e)}")