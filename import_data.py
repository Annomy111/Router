import json
from app import app, db, WohnquartierAnalyse

def recreate_tables():
    """Löscht und erstellt die Tabellen neu"""
    try:
        # Lösche alle Tabellen
        db.drop_all()
        print("Alle Tabellen wurden gelöscht")
        
        # Erstelle Tabellen neu
        db.create_all()
        print("Tabellen wurden neu erstellt")
    except Exception as e:
        print(f"Fehler beim Neuerstellen der Tabellen: {str(e)}")
        db.session.rollback()

def import_data():
    try:
        # Lese die Daten aus der JSON-Datei
        with open('initial_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Importiere jeden Datensatz
        for item in data:
            wohnquartier = WohnquartierAnalyse(
                Gemeinde=item['Gemeinde'],
                Haushalte=item['Haushalte'],
                Haushalte_zur_Miete=item['Haushalte_zur_Miete'],
                Haushalte_mit_Kindern=item['Haushalte_mit_Kindern']
            )
            db.session.add(wohnquartier)
        
        # Speichere die Änderungen
        db.session.commit()
        print(f"{len(data)} Datensätze wurden erfolgreich importiert")
        
        # Überprüfe die importierten Daten
        count = db.session.query(WohnquartierAnalyse).count()
        print(f"Anzahl der Datensätze in der Datenbank: {count}")
        
    except Exception as e:
        print(f"Fehler beim Importieren der Daten: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    with app.app_context():
        # Erstelle die Tabellen neu
        recreate_tables()
        # Importiere die Daten
        import_data() 