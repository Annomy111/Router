import sqlite3
import os
import json
from datetime import datetime

def backup_database():
    """Sichert die aktuelle Datenbank in eine JSON-Datei"""
    try:
        # Verbindung zur Datenbank herstellen
        conn = sqlite3.connect('instance/neue_daten.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Daten aus allen relevanten Tabellen abrufen
        backup_data = {
            'routes': [],
            'volunteers': [],
            'registrations': []
        }

        # Routen sichern
        cursor.execute('SELECT * FROM route')
        routes = cursor.fetchall()
        for route in routes:
            backup_data['routes'].append(dict(route))

        # Freiwillige sichern
        cursor.execute('SELECT * FROM volunteer')
        volunteers = cursor.fetchall()
        for volunteer in volunteers:
            backup_data['volunteers'].append(dict(volunteer))

        # Registrierungen sichern
        cursor.execute('SELECT * FROM route_registration')
        registrations = cursor.fetchall()
        for registration in registrations:
            backup_data['registrations'].append(dict(registration))

        # Backup in JSON-Datei speichern
        backup_file = 'instance/backup.json'
        os.makedirs('instance', exist_ok=True)
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)

        conn.close()
        return True

    except Exception as e:
        print(f"Fehler beim Backup: {str(e)}")
        return False

def restore_database():
    """Stellt die Datenbank aus der JSON-Backup-Datei wieder her"""
    try:
        backup_file = 'instance/backup.json'
        if not os.path.exists(backup_file):
            print("Kein Backup gefunden")
            return False

        # Backup-Daten laden
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)

        # Verbindung zur Datenbank herstellen
        conn = sqlite3.connect('instance/neue_daten.db')
        cursor = conn.cursor()

        # Routen wiederherstellen
        for route in backup_data['routes']:
            cursor.execute('''
                INSERT OR REPLACE INTO route 
                (id, city, street, house_numbers, zip_code, lat, lon, 
                mobilization_index, conviction_index, households, 
                rental_percentage, meeting_point, meeting_point_lat, 
                meeting_point_lon, is_active, needs_review)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                route['id'], route['city'], route['street'], 
                route['house_numbers'], route['zip_code'], route['lat'], 
                route['lon'], route['mobilization_index'], 
                route['conviction_index'], route['households'],
                route['rental_percentage'], route['meeting_point'], 
                route['meeting_point_lat'], route['meeting_point_lon'],
                True, route.get('needs_review', False)
            ))

        # Freiwillige wiederherstellen
        for volunteer in backup_data['volunteers']:
            cursor.execute('''
                INSERT OR REPLACE INTO volunteer 
                (id, name, email, phone)
                VALUES (?, ?, ?, ?)
            ''', (
                volunteer['id'], volunteer['name'], 
                volunteer['email'], volunteer['phone']
            ))

        # Registrierungen wiederherstellen
        for registration in backup_data['registrations']:
            cursor.execute('''
                INSERT OR REPLACE INTO route_registration 
                (id, route_id, volunteer_id, date, time_slot, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                registration['id'], registration['route_id'],
                registration['volunteer_id'], registration['date'],
                registration['time_slot'], registration['status']
            ))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"Fehler bei der Wiederherstellung: {str(e)}")
        return False

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