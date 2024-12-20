import sqlite3
from datetime import datetime

def create_registration_table():
    # Verbindung zur Datenbank herstellen
    conn = sqlite3.connect('neue_daten.db')
    cursor = conn.cursor()

    # Überprüfen, ob die Tabelle bereits existiert
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='registration'")
    if not cursor.fetchone():
        # Erstelle die Registration-Tabelle
        cursor.execute("""
            CREATE TABLE registration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id INTEGER NOT NULL,
                volunteer_id INTEGER NOT NULL,
                date DATE NOT NULL,
                time_slot VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'geplant',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (route_id) REFERENCES route (id),
                FOREIGN KEY (volunteer_id) REFERENCES user (id)
            )
        """)
        
        # Erstelle die Volunteer-Tabelle, falls sie noch nicht existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='volunteer'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE volunteer (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(120) NOT NULL UNIQUE,
                    phone VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    # Änderungen speichern
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_registration_table() 