import sqlite3
import json
import os

def export_data():
    # Verbindung zur SQLite-Datenbank herstellen
    conn = sqlite3.connect('neue_daten.db')
    cursor = conn.cursor()
    
    # Hole alle Daten aus der wohnquartier und excel_data Tabelle mit JOIN
    cursor.execute("""
        SELECT 
            w.*,
            e.WKR_SCHLUESSEL,
            e.WKR_NAME,
            e.WOHNQUART_SCHLUESSEL,
            e.MOBILISIERUNGSINDEX_KLASSE_WKR,
            e.UEBERZEUGUNSINDEX_KLASSE_WKR
        FROM wohnquartier w
        LEFT JOIN excel_data e ON w.Gemeinde = e.GEMEINDE_NAME
    """)
    wohnquartier_data = cursor.fetchall()
    
    # Hole die Spaltennamen
    cursor.execute("PRAGMA table_info(wohnquartier)")
    wohnquartier_columns = [col[1] for col in cursor.fetchall()]
    
    cursor.execute("PRAGMA table_info(excel_data)")
    excel_columns = [col[1] for col in cursor.fetchall()]
    
    # Erstelle eine Liste von Dictionaries für die Daten
    data = []
    for row in wohnquartier_data:
        data_dict = {}
        # Wohnquartier Daten
        for i, value in enumerate(row[:len(wohnquartier_columns)]):
            data_dict[wohnquartier_columns[i]] = value
        # Excel Daten
        for i, value in enumerate(row[len(wohnquartier_columns):]):
            if i < len(['WKR_SCHLUESSEL', 'WKR_NAME', 'WOHNQUART_SCHLUESSEL', 
                       'MOBILISIERUNGSINDEX_KLASSE_WKR', 'UEBERZEUGUNSINDEX_KLASSE_WKR']):
                data_dict[['WKR_SCHLUESSEL', 'WKR_NAME', 'WOHNQUART_SCHLUESSEL', 
                          'MOBILISIERUNGSINDEX_KLASSE_WKR', 'UEBERZEUGUNSINDEX_KLASSE_WKR'][i]] = value
        data.append(data_dict)
    
    # Berechne und zeige Statistiken
    print("\nStatistiken pro Gemeinde:")
    cursor.execute("""
        SELECT 
            Gemeinde,
            COUNT(*) as count,
            SUM(Haushalte) as total_households,
            AVG(CASE WHEN Haushalte > 0 THEN CAST(Haushalte_zur_Miete AS FLOAT) / Haushalte * 100 END) as avg_rent_quota,
            AVG(CASE WHEN Haushalte > 0 THEN CAST(Haushalte_mit_Kindern AS FLOAT) / Haushalte * 100 END) as avg_children_quota
        FROM wohnquartier
        GROUP BY Gemeinde
    """)
    stats = cursor.fetchall()
    for stat in stats:
        print(f"\n{stat[0]}:")
        print(f"  Anzahl Wohnquartiere: {stat[1]}")
        print(f"  Gesamtzahl Haushalte: {stat[2] if stat[2] is not None else 'Keine Daten'}")
        print(f"  Durchschnittliche Mietquote: {stat[3]:.1f}%" if stat[3] is not None else "  Durchschnittliche Mietquote: Keine Daten")
        print(f"  Durchschnittliche Kinderquote: {stat[4]:.1f}%" if stat[4] is not None else "  Durchschnittliche Kinderquote: Keine Daten")
    
    # Erstelle Verzeichnis für die Daten falls es nicht existiert
    os.makedirs('data', exist_ok=True)
    
    # Speichere die Daten in einer JSON-Datei im data Verzeichnis
    data_file = os.path.join('data', 'initial_data.json')
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\nDaten wurden in {data_file} exportiert")
    
    # Zeige eine Zusammenfassung der exportierten Daten
    print("\nZusammenfassung der exportierten Daten:")
    print(f"Anzahl der Datensätze: {len(data)}")
    gemeinden = set(d['Gemeinde'] for d in data)
    print("Enthaltene Gemeinden:", ", ".join(gemeinden))
    
    # Zeige Beispiele für Quartiersdetails
    print("\nBeispiele für Quartiersdetails:")
    for i, d in enumerate(data[:5]):
        print(f"\nQuartier {i+1}:")
        print(f"  Gemeinde: {d.get('Gemeinde', 'N/A')}")
        print(f"  Wahlkreis: {d.get('WKR_NAME', 'N/A')}")
        print(f"  Quartiersschlüssel: {d.get('WOHNQUART_SCHLUESSEL', 'N/A')}")
        print(f"  Haushalte: {d.get('Haushalte', 'N/A')}")
        print(f"  Haushalte zur Miete: {d.get('Haushalte_zur_Miete', 'N/A')}")
        print(f"  Haushalte mit Kindern: {d.get('Haushalte_mit_Kindern', 'N/A')}")
        print(f"  Mobilisierungsindex: {d.get('MOBILISIERUNGSINDEX_KLASSE_WKR', 'N/A')}")
        print(f"  Überzeugungsindex: {d.get('UEBERZEUGUNSINDEX_KLASSE_WKR', 'N/A')}")
    
    conn.close()

if __name__ == "__main__":
    export_data() 