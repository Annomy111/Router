import sqlite3
import pandas as pd
from typing import List, Dict
import os

class DatabaseAnalyzer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Verbindung zur Datenbank herstellen"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"Erfolgreich verbunden mit {self.db_path}")
        except sqlite3.Error as e:
            print(f"Fehler beim Verbinden zur Datenbank: {e}")
    
    def analyze_merge_issues(self):
        """Analysiert die Probleme beim Zusammenführen der Datensätze"""
        if not self.conn:
            self.connect()
            
        print("\nANALYSE DER DATENSÄTZE FÜR MERGE:")
        
        # 1. Analyse der Wohnquartier-Schlüssel
        print("\n1. WOHNQUARTIER-SCHLÜSSEL ANALYSE:")
        cursor = self.conn.cursor()
        
        # Prüfe Schlüssel in wohnquartier
        cursor.execute("""
            SELECT 
                SUBSTR(wq_key, 1, 7) as city_code,
                COUNT(*) as count,
                COUNT(DISTINCT wq_key) as unique_keys,
                COUNT(CASE WHEN Haushalte IS NOT NULL THEN 1 END) as with_data
            FROM wohnquartier
            GROUP BY SUBSTR(wq_key, 1, 7)
        """)
        
        print("\nSchlüssel in wohnquartier-Tabelle:")
        for row in cursor.fetchall():
            print(f"  Stadt {row[0]}: {row[1]} Einträge, {row[2]} unique, {row[3]} mit Daten")
            
        # Prüfe Schlüssel in excel_data
        cursor.execute("""
            SELECT 
                SUBSTR(WOHNQUART_SCHLUESSEL, 1, 7) as city_code,
                COUNT(*) as count,
                COUNT(DISTINCT WOHNQUART_SCHLUESSEL) as unique_keys,
                COUNT(DISTINCT GEMEINDE_NAME) as unique_cities
            FROM excel_data
            GROUP BY SUBSTR(WOHNQUART_SCHLUESSEL, 1, 7)
        """)
        
        print("\nSchlüssel in excel_data-Tabelle:")
        for row in cursor.fetchall():
            print(f"  Stadt {row[0]}: {row[1]} Einträge, {row[2]} unique, Gemeinden: {row[3]}")
            
        # 2. Vergleich der Schlüsselformate
        print("\n2. SCHLÜSSELFORMAT-ANALYSE:")
        cursor.execute("SELECT wq_key FROM wohnquartier LIMIT 5")
        wq_keys = cursor.fetchall()
        print("\nBeispiel Schlüssel aus wohnquartier:")
        for key in wq_keys:
            print(f"  {key[0]}")
            
        cursor.execute("SELECT WOHNQUART_SCHLUESSEL FROM excel_data LIMIT 5")
        excel_keys = cursor.fetchall()
        print("\nBeispiel Schlüssel aus excel_data:")
        for key in excel_keys:
            print(f"  {key[0]}")
            
        # 3. Prüfe auf nicht-gematchte Einträge
        print("\n3. NICHT-GEMATCHTE EINTRÄGE:")
        
        # Einträge in wohnquartier aber nicht in excel_data
        cursor.execute("""
            SELECT w.wq_key, w.Gemeinde
            FROM wohnquartier w
            LEFT JOIN excel_data e ON w.wq_key = e.WOHNQUART_SCHLUESSEL
            WHERE e.WOHNQUART_SCHLUESSEL IS NULL
            LIMIT 5
        """)
        print("\nBeispiel: In wohnquartier aber nicht in excel_data:")
        for row in cursor.fetchall():
            print(f"  {row[0]} - {row[1]}")
            
        # Einträge in excel_data aber nicht in wohnquartier
        cursor.execute("""
            SELECT e.WOHNQUART_SCHLUESSEL, e.GEMEINDE_NAME
            FROM excel_data e
            LEFT JOIN wohnquartier w ON e.WOHNQUART_SCHLUESSEL = w.wq_key
            WHERE w.wq_key IS NULL
            LIMIT 5
        """)
        print("\nBeispiel: In excel_data aber nicht in wohnquartier:")
        for row in cursor.fetchall():
            print(f"  {row[0]} - {row[1]}")
        
        # 4. Prüfe die Datentypen der Schlüssel
        print("\n4. DATENTYP-ANALYSE:")
        cursor.execute("""
            SELECT typeof(wq_key) as key_type, COUNT(*) as count
            FROM wohnquartier
            GROUP BY typeof(wq_key)
        """)
        print("\nDatentypen in wohnquartier.wq_key:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} Einträge")
            
        cursor.execute("""
            SELECT typeof(WOHNQUART_SCHLUESSEL) as key_type, COUNT(*) as count
            FROM excel_data
            GROUP BY typeof(WOHNQUART_SCHLUESSEL)
        """)
        print("\nDatentypen in excel_data.WOHNQUART_SCHLUESSEL:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} Einträge")
    
    def close(self):
        """Datenbankverbindung schließen"""
        if self.conn:
            self.conn.close()
            print("\nDatenbankverbindung geschlossen")

def main():
    analyzer = DatabaseAnalyzer('endergebnis.db')
    analyzer.analyze_merge_issues()
    analyzer.close()

if __name__ == "__main__":
    main() 