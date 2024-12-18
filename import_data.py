import json
from app import db, WohnquartierAnalyse

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
        
    except Exception as e:
        print(f"Fehler beim Importieren der Daten: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    # Erstelle die Tabellen
    db.create_all()
    # Importiere die Daten
    import_data() 