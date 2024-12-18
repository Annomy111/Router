import json
import os
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
        # Suche nach der JSON-Datei
        data_file = os.path.join('data', 'initial_data.json')
        if not os.path.exists(data_file):
            print(f"Datendatei {data_file} nicht gefunden!")
            return
        
        # Lese die Daten aus der JSON-Datei
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\nGefundene Datensätze: {len(data)}")
        
        # Importiere jeden Datensatz einzeln
        successful_imports = 0
        for item in data:
            try:
                wohnquartier = WohnquartierAnalyse(
                    Gemeinde=item['Gemeinde'],
                    Haushalte=item.get('Haushalte'),
                    Haushalte_zur_Miete=item.get('Haushalte_zur_Miete'),
                    Haushalte_mit_Kindern=item.get('Haushalte_mit_Kindern')
                )
                
                # Füge zusätzliche Felder hinzu, falls vorhanden
                for field in ['WKR_SCHLUESSEL', 'WKR_NAME', 'WOHNQUART_SCHLUESSEL',
                            'MOBILISIERUNGSINDEX_KLASSE_WKR', 'UEBERZEUGUNSINDEX_KLASSE_WKR']:
                    if field in item:
                        setattr(wohnquartier, field, item[field])
                
                db.session.add(wohnquartier)
                db.session.commit()
                successful_imports += 1
                
                # Zeige Fortschritt alle 100 Datensätze
                if successful_imports % 100 == 0:
                    print(f"Fortschritt: {successful_imports} von {len(data)} importiert")
                    
            except Exception as e:
                print(f"Fehler beim Importieren des Datensatzes {item.get('Gemeinde', 'UNBEKANNT')}: {str(e)}")
                db.session.rollback()
                continue
        
        print(f"\n{successful_imports} von {len(data)} Datensätzen wurden erfolgreich importiert")
        
        # Überprüfe die importierten Daten
        count = db.session.query(WohnquartierAnalyse).count()
        print(f"Anzahl der Datensätze in der Datenbank: {count}")
        
        # Zeige Beispieldaten mit allen verfügbaren Feldern
        print("\nBeispieldaten:")
        sample_data = db.session.query(WohnquartierAnalyse).limit(5).all()
        for item in sample_data:
            print(f"\nGemeinde: {item.Gemeinde}")
            print(f"  Haushalte: {item.Haushalte}")
            print(f"  Haushalte zur Miete: {item.Haushalte_zur_Miete}")
            print(f"  Haushalte mit Kindern: {item.Haushalte_mit_Kindern}")
            if hasattr(item, 'WKR_NAME'):
                print(f"  Wahlkreis: {item.WKR_NAME}")
            if hasattr(item, 'WOHNQUART_SCHLUESSEL'):
                print(f"  Quartiersschlüssel: {item.WOHNQUART_SCHLUESSEL}")
            if hasattr(item, 'MOBILISIERUNGSINDEX_KLASSE_WKR'):
                print(f"  Mobilisierungsindex: {item.MOBILISIERUNGSINDEX_KLASSE_WKR}")
            if hasattr(item, 'UEBERZEUGUNSINDEX_KLASSE_WKR'):
                print(f"  Überzeugungsindex: {item.UEBERZEUGUNSINDEX_KLASSE_WKR}")
        
    except Exception as e:
        print(f"Fehler beim Importieren der Daten: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    with app.app_context():
        # Erstelle die Tabellen neu
        recreate_tables()
        # Importiere die Daten
        import_data() 