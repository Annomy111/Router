# Administratorhandbuch

## Inhaltsverzeichnis
1. [Einführung](#einführung)
2. [Systemarchitektur](#systemarchitektur)
3. [Datenbank](#datenbank)
4. [Algorithmen und Logik](#algorithmen)
5. [Admin-Panel](#admin-panel)
6. [Wartung und Backup](#wartung)
7. [API-Dokumentation](#api)

## Einführung <a name="einführung"></a>
Dieses Handbuch richtet sich an Administratoren der Wahlkampf-Routen-App und enthält technische Details zur Verwaltung und Wartung des Systems.

## Systemarchitektur <a name="systemarchitektur"></a>

### Technologie-Stack
- Backend: Python Flask
- Datenbank: SQLite
- Frontend: HTML, CSS (Bootstrap), JavaScript
- Kartendienste: Google Maps API
- E-Mail: Flask-Mail mit SMTP

### Hauptkomponenten
1. Routenverwaltung
2. Benutzerverwaltung
3. Registrierungssystem
4. Kartendarstellung
5. E-Mail-Benachrichtigungen
6. Backup-System

## Datenbank <a name="datenbank"></a>

### Datenbankschema

#### Route
```sql
CREATE TABLE route (
    id INTEGER PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    zip_code VARCHAR(5),
    street VARCHAR(100) NOT NULL,
    house_numbers VARCHAR(50) NOT NULL,
    mobilization_index FLOAT NOT NULL,
    conviction_index FLOAT NOT NULL,
    households INTEGER,
    rental_percentage FLOAT,
    lat FLOAT NOT NULL,
    lon FLOAT NOT NULL,
    meeting_point VARCHAR(200),
    meeting_point_lat FLOAT,
    meeting_point_lon FLOAT,
    max_volunteers INTEGER DEFAULT 4,
    is_active BOOLEAN DEFAULT TRUE,
    needs_review BOOLEAN DEFAULT FALSE
)
```

#### Volunteer
```sql
CREATE TABLE volunteer (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone VARCHAR(20)
)
```

#### RouteRegistration
```sql
CREATE TABLE route_registration (
    id INTEGER PRIMARY KEY,
    volunteer_id INTEGER NOT NULL,
    route_id INTEGER NOT NULL,
    date DATE NOT NULL,
    time_slot VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'geplant',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (route_id) REFERENCES route(id),
    FOREIGN KEY (volunteer_id) REFERENCES volunteer(id)
)
```

### Backup-System
- Automatische Backups bei Serverbeendigung
- JSON-basiertes Backup-Format
- Wiederherstellungsfunktion beim Serverstart
- Backup-Dateien in `instance/backup.json`

## Algorithmen und Logik <a name="algorithmen"></a>

### Potenzialberechnung
```python
potential_score = (
    mietquote / 100 * 0.4 +              # Mietquote (40%)
    (kinderquote / 100) * 0.3 +          # Kinderquote (30%)
    (mobilisierungsindex / 3) * 0.3      # Mobilisierungsindex (30%)
)
```

### Routenpriorisierung
- Basiert auf kombiniertem Score aus:
  1. Mobilisierungsindex (0-3)
  2. Überzeugungsindex (0-3)
  3. Mietquote (%)
  4. Anzahl Haushalte

### Registrierungslogik
1. Prüfung der maximalen Teilnehmer
2. Zeitslot-Verfügbarkeit
3. Doppelregistrierungsprävention
4. Automatische E-Mail-Benachrichtigungen

## Admin-Panel <a name="admin-panel"></a>

### Zugriff
1. Login unter `/login`
2. Standard-Credentials:
   - Benutzer: admin
   - Passwort: admin123 (bitte ändern!)

### Funktionen
1. Routenverwaltung
   - Aktivieren/Deaktivieren von Routen
   - Status-Übersicht
   - Bearbeitung der Routendetails

2. Registrierungsverwaltung
   - Übersicht aller Registrierungen
   - Status-Updates (geplant/abgeschlossen/abgesagt)
   - Freiwilligen-Informationen

3. Statistiken
   - Aktive Routen
   - Registrierte Helfer
   - Gebuchte Termine
   - Abschlussquote

## Wartung und Backup <a name="wartung"></a>

### Datenbank-Wartung
1. Backup erstellen:
   ```bash
   python backup_db.py
   ```

2. Backup wiederherstellen:
   ```bash
   python backup_db.py restore
   ```

3. Datenbank zurücksetzen:
   ```bash
   rm instance/neue_daten.db
   python init_db.py
   ```

### Migrationen
- Neue Spalten: `migrations/add_route_fields.py`
- Meeting Points: `migrations/add_meeting_point.py`
- Max Volunteers: `migrations/add_max_volunteers.py`

### Monitoring
- Fehlerprotokolle in der Konsole
- E-Mail-Versand-Status
- Registrierungsstatistiken im Admin-Panel

## API-Dokumentation <a name="api"></a>

### Routen-API
```python
GET /api/routes
- Liefert alle aktiven Routen

POST /api/routes/<route_id>/toggle
- Aktiviert/Deaktiviert eine Route

GET /api/route-data
- Liefert detaillierte Routendaten mit Statistiken
```

### Registrierungs-API
```python
POST /api/register
- Neue Registrierung erstellen

POST /api/registrations/<reg_id>/status
- Status einer Registrierung aktualisieren
```

### Fehlerbehandlung
- HTTP-Statuscodes
- JSON-Fehlermeldungen
- Logging ins Konsolensystem

### Sicherheit
- Flask-Login für Authentifizierung
- CSRF-Schutz
- Eingabevalidierung
- Berechtigungsprüfungen 