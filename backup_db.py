import sqlite3
import json
from datetime import datetime
import os
import glob

def backup_database():
    """Erstellt ein Backup der Datenbank"""
    try:
        # Verbindung zur Datenbank herstellen
        conn = sqlite3.connect('instance/neue_daten.db')
        cursor = conn.cursor()
        
        # Hole alle Routen
        cursor.execute("""
            SELECT id, street, house_numbers, zip_code, city, lat, lon, 
                   mobilization_index, conviction_index, households, rental_percentage,
                   meeting_point, meeting_point_lat, meeting_point_lon, is_active, needs_review
            FROM route
        """)
        routes = cursor.fetchall()
        
        # Hole alle Freiwilligen
        cursor.execute("""
            SELECT id, name, email, phone
            FROM volunteer
        """)
        volunteers = cursor.fetchall()
        
        # Hole alle Registrierungen
        cursor.execute("""
            SELECT id, volunteer_id, route_id, date, time_slot, status
            FROM route_registration
        """)
        registrations = cursor.fetchall()
        
        # Erstelle Backup-Verzeichnis, falls es nicht existiert
        if not os.path.exists('backups'):
            os.makedirs('backups')
        
        # Erstelle Backup-Datei
        backup_data = {
            'routes': [{
                'id': r[0],
                'street': r[1],
                'house_numbers': r[2],
                'zip_code': r[3],
                'city': r[4],
                'lat': r[5],
                'lon': r[6],
                'mobilization_index': r[7],
                'conviction_index': r[8],
                'households': r[9],
                'rental_percentage': r[10],
                'meeting_point': r[11],
                'meeting_point_lat': r[12],
                'meeting_point_lon': r[13],
                'is_active': bool(r[14]),
                'needs_review': bool(r[15])
            } for r in routes],
            'volunteers': [{
                'id': v[0],
                'name': v[1],
                'email': v[2],
                'phone': v[3]
            } for v in volunteers],
            'registrations': [{
                'id': reg[0],
                'volunteer_id': reg[1],
                'route_id': reg[2],
                'date': reg[3],
                'time_slot': reg[4],
                'status': reg[5]
            } for reg in registrations]
        }
        
        # Speichere Backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'backups/db_backup_{timestamp}.json'
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=4)
        
        print(f"Backup wurde erstellt: {backup_file}")
        return backup_file
        
    except Exception as e:
        print(f"Fehler beim Erstellen des Backups: {str(e)}")
        return None

def restore_database():
    """Stellt die Datenbank aus dem neuesten Backup wieder her"""
    try:
        # Finde das neueste Backup
        backup_files = glob.glob('backups/db_backup_*.json')
        if not backup_files:
            print("Keine Backup-Dateien gefunden")
            return
        
        latest_backup = max(backup_files)
        
        # Lade Backup-Daten
        with open(latest_backup, 'r') as f:
            backup_data = json.load(f)
        
        # Verbindung zur Datenbank herstellen
        conn = sqlite3.connect('instance/neue_daten.db')
        cursor = conn.cursor()
        
        # Stelle Routen wieder her
        for route in backup_data['routes']:
            cursor.execute("""
                INSERT OR REPLACE INTO route 
                (id, street, house_numbers, zip_code, city, lat, lon,
                 mobilization_index, conviction_index, households, rental_percentage,
                 meeting_point, meeting_point_lat, meeting_point_lon, is_active, needs_review)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                route['id'], route['street'], route['house_numbers'], route['zip_code'],
                route['city'], route['lat'], route['lon'], route['mobilization_index'],
                route['conviction_index'], route['households'], route['rental_percentage'],
                route['meeting_point'], route['meeting_point_lat'], route['meeting_point_lon'],
                route['is_active'], route['needs_review']
            ))
        
        # Stelle Freiwillige wieder her
        for volunteer in backup_data['volunteers']:
            cursor.execute("""
                INSERT OR REPLACE INTO volunteer 
                (id, name, email, phone)
                VALUES (?, ?, ?, ?)
            """, (
                volunteer['id'], volunteer['name'], volunteer['email'], volunteer['phone']
            ))
        
        # Stelle Registrierungen wieder her
        for reg in backup_data['registrations']:
            cursor.execute("""
                INSERT OR REPLACE INTO route_registration 
                (id, volunteer_id, route_id, date, time_slot, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                reg['id'], reg['volunteer_id'], reg['route_id'],
                reg['date'], reg['time_slot'], reg['status']
            ))
        
        conn.commit()
        print(f"Datenbank erfolgreich wiederhergestellt aus {latest_backup}")
        
    except Exception as e:
        print(f"Fehler beim Wiederherstellen der Datenbank: {str(e)}")
        if 'conn' in locals():
            conn.rollback()

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