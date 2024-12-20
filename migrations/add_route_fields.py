"""Add zip_code and path_coordinates to routes

Revision ID: add_route_fields
"""
from alembic import op
import sqlalchemy as sa
import sqlite3

def upgrade():
    # Füge die neuen Spalten hinzu
    op.add_column('route', sa.Column('zip_code', sa.String(5), nullable=True))
    op.add_column('route', sa.Column('path_coordinates', sa.JSON, nullable=True))
    
    # Aktualisiere bestehende Routen mit Postleitzahlen
    update_routes()

def downgrade():
    op.drop_column('route', 'zip_code')
    op.drop_column('route', 'path_coordinates') 

def update_routes():
    # Verbindung zur Datenbank herstellen
    conn = sqlite3.connect('neue_daten.db')
    cursor = conn.cursor()

    # Postleitzahlen für die Städte
    zip_codes = {
        'Moers': '47441',
        'Krefeld': '47798',
        'Neukirchen-Vluyn': '47506'
    }

    # Überprüfen, ob die Spalte zip_code bereits existiert
    cursor.execute("PRAGMA table_info(route)")
    columns = cursor.fetchall()
    if 'zip_code' not in [col[1] for col in columns]:
        cursor.execute("""
            ALTER TABLE route 
            ADD COLUMN zip_code VARCHAR(5)
        """)

    # Überprüfen, ob die Spalte path_coordinates bereits existiert
    if 'path_coordinates' not in [col[1] for col in columns]:
        cursor.execute("""
            ALTER TABLE route 
            ADD COLUMN path_coordinates JSON
        """)

    # Postleitzahlen für bestehende Routen aktualisieren
    for city, zip_code in zip_codes.items():
        cursor.execute("""
            UPDATE route 
            SET zip_code = ? 
            WHERE city = ? AND (zip_code IS NULL OR zip_code = '')
        """, (zip_code, city))

    # Änderungen speichern
    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_routes() 