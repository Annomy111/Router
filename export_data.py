import sqlite3
import json

def export_data():
    # Verbindung zur SQLite-Datenbank herstellen
    conn = sqlite3.connect('neue_daten.db')
    cursor = conn.cursor()
    
    # Hole alle Daten aus der wohnquartier-Tabelle
    cursor.execute("SELECT * FROM wohnquartier")
    wohnquartier_data = cursor.fetchall()
    
    # Hole die Spaltennamen
    cursor.execute("PRAGMA table_info(wohnquartier)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Erstelle eine Liste von Dictionaries für die Daten
    data = []
    for row in wohnquartier_data:
        data_dict = {}
        for i, value in enumerate(row):
            data_dict[columns[i]] = value
        data.append(data_dict)
    
    # Speichere die Daten in einer JSON-Datei
    with open('initial_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Daten wurden in initial_data.json exportiert")
    
    conn.close()

if __name__ == "__main__":
    export_data() 