import sqlite3
import pandas as pd
from typing import List, Dict
import os

class DatabaseMerger:
    def __init__(self, source_db: str, target_db: str):
        self.source_db = source_db
        self.target_db = target_db
        self.source_conn = None
        self.target_conn = None
        
    def connect(self):
        """Verbindungen zu Datenbanken herstellen"""
        try:
            self.source_conn = sqlite3.connect(self.source_db)
            print(f"Verbunden mit Quelldatenbank: {self.source_db}")
            
            # Neue Zieldatenbank erstellen
            self.target_conn = sqlite3.connect(self.target_db)
            print(f"Neue Zieldatenbank erstellt: {self.target_db}")
            
        except sqlite3.Error as e:
            print(f"Fehler beim Verbinden zur Datenbank: {e}")
    
    def copy_source_tables(self):
        """Kopiert die Quelltabellen in die neue Datenbank"""
        print("\nKOPIERE QUELLTABELLEN:")
        
        # Lese die Daten aus der Quelldatenbank
        wohnquartier_df = pd.read_sql_query("SELECT * FROM wohnquartier", self.source_conn)
        excel_data_df = pd.read_sql_query("SELECT * FROM excel_data", self.source_conn)
        
        # Speichere in der neuen Datenbank
        wohnquartier_df.to_sql('wohnquartier', self.target_conn, if_exists='replace', index=False)
        excel_data_df.to_sql('excel_data', self.target_conn, if_exists='replace', index=False)
        
        print("Quelltabellen kopiert")
    
    def standardize_keys(self):
        """Standardisiert die Schlüssel in beiden Tabellen"""
        print("\n1. STANDARDISIERE SCHLÜSSEL:")
        
        # Erstelle temporäre Tabelle für wohnquartier mit standardisierten Schlüsseln
        self.target_conn.execute("""
            CREATE TABLE wohnquartier_temp AS
            SELECT 
                CASE 
                    WHEN LENGTH(wq_key) = 13 THEN '0' || SUBSTR(wq_key, 2)
                    ELSE wq_key 
                END as wq_key,
                *
            FROM wohnquartier
        """)
        
        # Erstelle temporäre Tabelle für excel_data mit standardisierten Schlüsseln
        self.target_conn.execute("""
            CREATE TABLE excel_data_temp AS
            SELECT 
                CASE 
                    WHEN LENGTH(WOHNQUART_SCHLUESSEL) = 12 THEN '0' || WOHNQUART_SCHLUESSEL
                    ELSE WOHNQUART_SCHLUESSEL 
                END as WOHNQUART_SCHLUESSEL,
                *
            FROM excel_data
            WHERE WOHNQUART_SCHLUESSEL IS NOT NULL
        """)
        
        print("Schlüssel standardisiert")
    
    def merge_data(self):
        """Führt die Daten zusammen"""
        print("\n2. FÜHRE DATEN ZUSAMMEN:")
        
        # Erstelle die finale Tabelle mit LEFT JOIN
        self.target_conn.execute("""
            CREATE TABLE wohnquartiere_final AS
            SELECT 
                w.wq_key,
                COALESCE(w.Gemeinde, e.GEMEINDE_NAME) as Gemeinde,
                w.Haushalte,
                w.Haushalte_zur_Miete,
                w.Haushalte_mit_Kindern,
                w.Einwohner,
                w.Rentner_innen,
                w.Erwerbstaetige,
                w.Erwerbstaetigenquote,
                w.Kaufkraft_pro_Einwohner,
                w.Migrationshintergrund,
                w.Erstwaehler_innen,
                w.Auszubildende,
                w.Studierende,
                e.WKR_SCHLUESSEL,
                e.WKR_NAME,
                e.MOBILISIERUNGSINDEX_KLASSE_WKR,
                e.UEBERZEUGUNSINDEX_KLASSE_WKR
            FROM wohnquartier_temp w
            LEFT JOIN excel_data_temp e ON w.wq_key = e.WOHNQUART_SCHLUESSEL
        """)
        
        # Füge fehlende Einträge aus excel_data hinzu
        self.target_conn.execute("""
            INSERT INTO wohnquartiere_final
            SELECT 
                e.WOHNQUART_SCHLUESSEL as wq_key,
                e.GEMEINDE_NAME as Gemeinde,
                NULL as Haushalte,
                NULL as Haushalte_zur_Miete,
                NULL as Haushalte_mit_Kindern,
                NULL as Einwohner,
                NULL as Rentner_innen,
                NULL as Erwerbstaetige,
                NULL as Erwerbstaetigenquote,
                NULL as Kaufkraft_pro_Einwohner,
                NULL as Migrationshintergrund,
                NULL as Erstwaehler_innen,
                NULL as Auszubildende,
                NULL as Studierende,
                e.WKR_SCHLUESSEL,
                e.WKR_NAME,
                e.MOBILISIERUNGSINDEX_KLASSE_WKR,
                e.UEBERZEUGUNSINDEX_KLASSE_WKR
            FROM excel_data_temp e
            LEFT JOIN wohnquartier_temp w ON e.WOHNQUART_SCHLUESSEL = w.wq_key
            WHERE w.wq_key IS NULL
        """)
        
        print("Daten zusammengeführt")
    
    def verify_merge(self):
        """Überprüft die Qualität des Merges"""
        print("\n3. ÜBERPRÜFE MERGE-QUALITÄT:")
        
        cursor = self.target_conn.cursor()
        
        # Prüfe Gesamtanzahl der Einträge
        cursor.execute("SELECT COUNT(*) FROM wohnquartiere_final")
        total = cursor.fetchone()[0]
        print(f"Gesamtanzahl Einträge: {total}")
        
        # Prüfe vollständige Datensätze
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN Haushalte IS NOT NULL THEN 1 ELSE 0 END) as with_households,
                SUM(CASE WHEN MOBILISIERUNGSINDEX_KLASSE_WKR IS NOT NULL THEN 1 ELSE 0 END) as with_mobil
            FROM wohnquartiere_final
        """)
        stats = cursor.fetchone()
        print(f"Einträge mit Haushaltsdaten: {stats[1]} von {stats[0]}")
        print(f"Einträge mit Mobilisierungsindex: {stats[2]} von {stats[0]}")
        
        # Prüfe nach Städten
        cursor.execute("""
            SELECT 
                Gemeinde,
                COUNT(*) as total,
                SUM(CASE WHEN Haushalte IS NOT NULL THEN 1 ELSE 0 END) as with_households,
                SUM(CASE WHEN MOBILISIERUNGSINDEX_KLASSE_WKR IS NOT NULL THEN 1 ELSE 0 END) as with_mobil
            FROM wohnquartiere_final
            WHERE Gemeinde IS NOT NULL
            GROUP BY Gemeinde
        """)
        
        print("\nAnalyse nach Städten:")
        for row in cursor.fetchall():
            print(f"\n{row[0]}:")
            print(f"  Gesamtanzahl Wohnquartiere: {row[1]}")
            print(f"  Mit Haushaltsdaten: {row[2]}")
            print(f"  Mit Mobilisierungsindex: {row[3]}")
    
    def execute_merge(self):
        """Führt den gesamten Merge-Prozess durch"""
        self.connect()
        self.copy_source_tables()
        self.standardize_keys()
        self.merge_data()
        self.verify_merge()
        
        # Speichere die Änderungen
        self.target_conn.commit()
        print("\nMerge abgeschlossen und gespeichert")
        
        self.close()
    
    def close(self):
        """Schließt die Datenbankverbindungen"""
        if self.source_conn:
            self.source_conn.close()
        if self.target_conn:
            self.target_conn.close()
        print("\nDatenbankverbindungen geschlossen")

def main():
    merger = DatabaseMerger('endergebnis.db', 'endergebnis_merged.db')
    merger.execute_merge()

if __name__ == "__main__":
    main() 