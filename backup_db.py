import sqlite3
import json
from datetime import datetime
import os

def backup_database():
    """Sichert die wichtigen Daten aus der Datenbank"""
    try:
        conn = sqlite3.connect('instance/neue_daten.db')
        cursor = conn.cursor()
        
        # Backup-Verzeichnis erstellen, falls es nicht existiert
        if not os.path.exists('backups'):
            os.makedirs('backups')
        
        backup_data = {
            'route_registrations': [],
            'volunteers': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Registrierungen sichern
        try:
            cursor.execute("""
                SELECT id, route_id, volunteer_id, date, time_slot, status, created_at 
                FROM route_registration
            """)
            registrations = cursor.fetchall()
            for reg in registrations:
                backup_data['route_registrations'].append({
                    'id': reg[0],
                    'route_id': reg[1],
                    'volunteer_id': reg[2],
                    'date': reg[3],
                    'time_slot': reg[4],
                    'status': reg[5],
                    'created_at': reg[6]
                })
        except sqlite3.OperationalError:
            print("Warnung: Tabelle route_registration existiert noch nicht")
        
        # Freiwillige sichern
        try:
            cursor.execute("""
                SELECT id, name, email, phone 
                FROM volunteer
            """)
            volunteers = cursor.fetchall()
            for vol in volunteers:
                backup_data['volunteers'].append({
                    'id': vol[0],
                    'name': vol[1],
                    'email': vol[2],
                    'phone': vol[3]
                })
        except sqlite3.OperationalError:
            print("Warnung: Tabelle volunteer existiert noch nicht")
        
        # Backup in Datei speichern
        backup_file = f"backups/db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        conn.close()
        return backup_file
    except Exception as e:
        print(f"Fehler beim Backup der Datenbank: {str(e)}")
        return None

def restore_database(backup_file=None):
    """Stellt die Daten aus dem letzten Backup wieder her"""
    if backup_file is None:
        # Finde das neueste Backup
        if not os.path.exists('backups'):
            print("Kein Backup-Verzeichnis gefunden.")
            return
        backup_files = [f for f in os.listdir('backups') if f.startswith('db_backup_')]
        if not backup_files:
            print("Kein Backup gefunden.")
            return
        backup_file = f"backups/{sorted(backup_files)[-1]}"
    
    try:
        # Lade das Backup
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        conn = sqlite3.connect('instance/neue_daten.db')
        cursor = conn.cursor()
        
        # Stelle sicher, dass die Tabellen existieren
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS volunteer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(120) NOT NULL UNIQUE,
                phone VARCHAR(20)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS route_registration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id INTEGER NOT NULL,
                volunteer_id INTEGER NOT NULL,
                date DATE NOT NULL,
                time_slot VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'geplant',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (route_id) REFERENCES route (id),
                FOREIGN KEY (volunteer_id) REFERENCES volunteer (id)
            )
        """)
        
        # Stelle die Freiwilligen wieder her
        for vol in backup_data.get('volunteers', []):
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO volunteer 
                    (id, name, email, phone)
                    VALUES (?, ?, ?, ?)
                """, (vol['id'], vol['name'], vol['email'], vol['phone']))
            except sqlite3.Error as e:
                print(f"Fehler beim Wiederherstellen des Freiwilligen {vol['name']}: {e}")
        
        # Stelle die Registrierungen wieder her
        for reg in backup_data.get('route_registrations', []):
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO route_registration 
                    (id, route_id, volunteer_id, date, time_slot, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (reg['id'], reg['route_id'], reg['volunteer_id'], reg['date'], 
                     reg['time_slot'], reg['status'], reg['created_at']))
            except sqlite3.Error as e:
                print(f"Fehler beim Wiederherstellen der Registrierung {reg['id']}: {e}")
        
        conn.commit()
        conn.close()
        print(f"Datenbank erfolgreich wiederhergestellt aus {backup_file}")
    except Exception as e:
        print(f"Fehler beim Wiederherstellen der Datenbank: {str(e)}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        restore_database()
    else:
        backup_file = backup_database()
        if backup_file:
            print(f"Backup erstellt: {backup_file}")
        else:
            print("Backup fehlgeschlagen") 