import pandas as pd
import sqlite3
import tabula
import os
import jpype
import logging
import numpy as np
import pdfplumber
import re
from typing import Dict, List, Any

# Konfiguriere Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataImporter:
    def __init__(self, pdf_path: str, excel_path: str, db_path: str):
        self.pdf_path = pdf_path
        self.excel_path = excel_path
        self.db_path = db_path
        self.conn = None
        
        # Definiere erwartete Wertebereiche
        self.value_ranges = {
            'Haushalte': (0, 10000),
            'Haushalte_zur_Miete': (0, 10000),
            'Haushalte_mit_Kindern': (0, 5000),
            'Einwohner': (0, 30000),
            'Rentner_innen': (0, 10000),
            'Erwerbstaetige': (0, 20000),
            'Erwerbstaetigenquote': (0, 1),
            'Kaufkraft_pro_Einwohner': (10000, 100000),
            'Migrationshintergrund': (0, 10000),
            'Erstwaehler_innen': (0, 1000)
        }
        
    def connect_db(self):
        """Verbindung zur Datenbank herstellen"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            logger.info(f"Verbunden mit Datenbank: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Fehler beim Verbinden zur Datenbank: {e}")
    
    def clean_value(self, value_str: str, field_name: str = None) -> Any:
        """Bereinigt einen Wert und konvertiert ihn in eine Zahl"""
        if pd.isna(value_str) or value_str == '':
            return None
            
        try:
            # Entferne Tausendertrennzeichen und ersetze Dezimalkomma
            cleaned = str(value_str).replace('.', '').replace(',', '.')
            # Entferne alle nicht-numerischen Zeichen (außer Dezimalpunkt)
            cleaned = re.sub(r'[^\d.]', '', cleaned)
            
            # Konvertiere in Zahl
            if '.' in cleaned:
                value = float(cleaned)
            else:
                value = int(cleaned)
            
            # Prüfe Wertebereich falls bekannt
            if field_name and field_name in self.value_ranges:
                min_val, max_val = self.value_ranges[field_name]
                if not min_val <= value <= max_val:
                    logger.warning(f"Wert {value} für {field_name} außerhalb des erwarteten Bereichs [{min_val}, {max_val}]")
                    return None
            
            return value
            
        except (ValueError, TypeError):
            return None
    
    def standardize_city_name(self, name: str) -> str:
        """Standardisiert den Städtenamen"""
        if not name:
            return name
            
        # Entferne überflüssige Leerzeichen
        name = ' '.join(name.split())
        
        # Standardisiere bekannte Varianten
        name_mapping = {
            'Moers,Stadt': 'Moers, Stadt',
            'Moers': 'Moers, Stadt',
            'Krefeld': 'Krefeld, Stadt',
            'Neukirchen Vluyn': 'Neukirchen-Vluyn, Stadt',
            'Neukirchen-Vluyn': 'Neukirchen-Vluyn, Stadt'
        }
        
        return name_mapping.get(name, name)
    
    def validate_data(self, data: Dict) -> bool:
        """Validiert einen Datensatz"""
        if not data.get('Gemeinde'):
            return False
            
        # Prüfe ob mindestens ein Wert vorhanden ist
        has_value = False
        for key, value in data.items():
            if key != 'Gemeinde' and value is not None:
                has_value = True
                break
        
        return has_value
    
    def extract_data_from_text(self, text: str) -> List[Dict]:
        """Extrahiert die Daten aus dem Text"""
        data = []
        current_row = {}
        
        # Teile den Text in Zeilen
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Suche nach Gemeinde und Haushaltsdaten
            if "Gemeinde:" in line:
                if current_row and self.validate_data(current_row):
                    data.append(current_row)
                current_row = {}
                
                # Extrahiere die Daten
                parts = line.split('|')
                for part in parts:
                    part = part.strip()
                    try:
                        if "Gemeinde:" in part:
                            gemeinde = part.split(':')[1].strip()
                            current_row['Gemeinde'] = self.standardize_city_name(gemeinde)
                        elif "Haushalte:" in part:
                            current_row['Haushalte'] = self.clean_value(part.split(':')[1].strip(), 'Haushalte')
                        elif "Haushalte zur Miete:" in part:
                            current_row['Haushalte_zur_Miete'] = self.clean_value(part.split(':')[1].strip(), 'Haushalte_zur_Miete')
                        elif "Haushalte mit Kindern:" in part:
                            current_row['Haushalte_mit_Kindern'] = self.clean_value(part.split(':')[1].strip(), 'Haushalte_mit_Kindern')
                        elif "Einwohner:" in part:
                            current_row['Einwohner'] = self.clean_value(part.split(':')[1].strip(), 'Einwohner')
                        elif "Rentner_innen:" in part:
                            current_row['Rentner_innen'] = self.clean_value(part.split(':')[1].strip(), 'Rentner_innen')
                        elif "Erwerbstätige:" in part:
                            current_row['Erwerbstaetige'] = self.clean_value(part.split(':')[1].strip(), 'Erwerbstaetige')
                        elif "Erwerbstätigenquote:" in part:
                            current_row['Erwerbstaetigenquote'] = self.clean_value(part.split(':')[1].strip(), 'Erwerbstaetigenquote')
                        elif "Kaufkraft pro Einwohner:" in part:
                            current_row['Kaufkraft_pro_Einwohner'] = self.clean_value(part.split(':')[1].strip(), 'Kaufkraft_pro_Einwohner')
                        elif "Migrationshintergrund:" in part:
                            current_row['Migrationshintergrund'] = self.clean_value(part.split(':')[1].strip(), 'Migrationshintergrund')
                        elif "Erstwähler_innen:" in part:
                            current_row['Erstwaehler_innen'] = self.clean_value(part.split(':')[1].strip(), 'Erstwaehler_innen')
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Fehler beim Parsen von '{part}': {str(e)}")
                        continue
        
        # Füge die letzte Zeile hinzu
        if current_row and self.validate_data(current_row):
            data.append(current_row)
        
        return data
    
    def clean_excel_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Bereinigt die Excel-Daten"""
        # Standardisiere Städtenamen
        df['GEMEINDE_NAME'] = df['GEMEINDE_NAME'].apply(self.standardize_city_name)
        
        # Entferne Zeilen ohne Schlüssel
        df = df.dropna(subset=['WOHNQUART_SCHLUESSEL'])
        
        # Konvertiere Indizes in Zahlen
        df['MOBILISIERUNGSINDEX_KLASSE_WKR'] = pd.to_numeric(df['MOBILISIERUNGSINDEX_KLASSE_WKR'], errors='coerce')
        df['UEBERZEUGUNSINDEX_KLASSE_WKR'] = pd.to_numeric(df['UEBERZEUGUNSINDEX_KLASSE_WKR'], errors='coerce')
        
        return df
    
    def import_pdf(self):
        """Importiert die Daten aus der PDF"""
        logger.info("\nIMPORTIERE PDF-DATEN:")
        
        try:
            # Prüfe ob die PDF existiert
            if not os.path.exists(self.pdf_path):
                logger.error(f"PDF-Datei nicht gefunden: {self.pdf_path}")
                return None
            
            logger.info("Lese PDF...")
            logger.info(f"PDF-Pfad: {os.path.abspath(self.pdf_path)}")
            
            # Lese den Text aus der PDF
            all_text = ""
            with pdfplumber.open(self.pdf_path) as pdf:
                logger.info(f"Anzahl Seiten: {len(pdf.pages)}")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    logger.info(f"Verarbeite Seite {page_num}...")
                    text = page.extract_text()
                    if text:
                        all_text += text + "\n"
            
            if not all_text:
                logger.error("Keine Textdaten in der PDF gefunden!")
                return None
            
            # Extrahiere die Daten aus dem Text
            data = self.extract_data_from_text(all_text)
            
            if not data:
                logger.error("Keine verwertbaren Daten gefunden!")
                return None
            
            # Erstelle DataFrame
            df = pd.DataFrame(data)
            
            # Validiere die Daten
            total_rows = len(df)
            valid_rows = df.dropna(subset=['Haushalte']).shape[0]
            logger.info(f"\nDatenqualität:")
            logger.info(f"  Gesamtanzahl Zeilen: {total_rows}")
            logger.info(f"  Zeilen mit Haushaltsdaten: {valid_rows}")
            logger.info(f"  Datenqualität: {(valid_rows/total_rows*100):.1f}%")
            
            # Zeige die Ergebnisse
            logger.info("\nGefundene Spalten:")
            for col in df.columns:
                non_null = df[col].count()
                logger.info(f"  - {col}: {non_null} Werte ({(non_null/total_rows*100):.1f}% gefüllt)")
            
            # Zeige die ersten Zeilen
            logger.info("\nErste Zeilen der Daten:")
            logger.info(df.head().to_string())
            
            # Speichere in der Datenbank
            df.to_sql('wohnquartier', self.conn, if_exists='replace', index=False)
            logger.info("PDF-Daten in Datenbank gespeichert")
            
            return df
            
        except Exception as e:
            logger.error(f"Fehler beim PDF-Import: {str(e)}", exc_info=True)
            return None
    
    def import_excel(self):
        """Importiert die Daten aus der Excel-Datei"""
        logger.info("\nIMPORTIERE EXCEL-DATEN:")
        
        try:
            # Prüfe ob die Excel-Datei existiert
            if not os.path.exists(self.excel_path):
                logger.error(f"Excel-Datei nicht gefunden: {self.excel_path}")
                return None
            
            # Lese die Excel-Datei
            logger.info("Lese Excel...")
            df = pd.read_excel(self.excel_path)
            
            # Bereinige die Daten
            df = self.clean_excel_data(df)
            
            # Validiere die Daten
            total_rows = len(df)
            valid_rows = df.dropna(subset=['WOHNQUART_SCHLUESSEL', 'GEMEINDE_NAME']).shape[0]
            logger.info(f"\nDatenqualität:")
            logger.info(f"  Gesamtanzahl Zeilen: {total_rows}")
            logger.info(f"  Gültige Zeilen: {valid_rows}")
            logger.info(f"  Datenqualität: {(valid_rows/total_rows*100):.1f}%")
            
            # Zeige die ersten Zeilen und Spalten
            logger.info("\nGefundene Spalten:")
            for col in df.columns:
                non_null = df[col].count()
                logger.info(f"  - {col}: {non_null} Werte ({(non_null/total_rows*100):.1f}% gefüllt)")
            
            # Zeige die ersten Zeilen
            logger.info("\nErste Zeilen der Daten:")
            logger.info(df.head().to_string())
            
            # Speichere in der Datenbank
            df.to_sql('excel_data', self.conn, if_exists='replace', index=False)
            logger.info("Excel-Daten in Datenbank gespeichert")
            
            return df
            
        except Exception as e:
            logger.error(f"Fehler beim Excel-Import: {str(e)}", exc_info=True)
            return None
    
    def merge_data(self):
        """Führt die Daten aus PDF und Excel zusammen"""
        logger.info("\nFÜHRE DATEN ZUSAMMEN:")
        
        try:
            # Lade die Daten aus der Datenbank
            pdf_data = pd.read_sql_query("SELECT * FROM wohnquartier", self.conn)
            excel_data = pd.read_sql_query("SELECT * FROM excel_data", self.conn)
            
            # Gruppiere die PDF-Daten nach Gemeinde
            pdf_stats = pdf_data.groupby('Gemeinde').agg({
                'Haushalte': ['count', 'sum', 'mean', 'min', 'max'],
                'Haushalte_zur_Miete': ['count', 'sum', 'mean', 'min', 'max'],
                'Haushalte_mit_Kindern': ['count', 'sum', 'mean', 'min', 'max']
            }).round(1)
            
            # Gruppiere die Excel-Daten nach Gemeinde
            excel_stats = excel_data.groupby('GEMEINDE_NAME').agg({
                'WOHNQUART_SCHLUESSEL': ['count', 'nunique'],
                'MOBILISIERUNGSINDEX_KLASSE_WKR': ['count', 'mean', 'min', 'max'],
                'UEBERZEUGUNSINDEX_KLASSE_WKR': ['count', 'mean', 'min', 'max']
            }).round(2)
            
            logger.info("\nStatistiken aus PDF-Daten:")
            logger.info(pdf_stats.to_string())
            
            logger.info("\nStatistiken aus Excel-Daten:")
            logger.info(excel_stats.to_string())
            
            # Speichere die Statistiken
            pdf_stats.to_sql('pdf_statistics', self.conn, if_exists='replace')
            excel_stats.to_sql('excel_statistics', self.conn, if_exists='replace')
            
            # Vergleiche die Anzahl der Datensätze
            comparison = pd.DataFrame({
                'PDF_Datensätze': pdf_data.groupby('Gemeinde').size(),
                'Excel_Datensätze': excel_data.groupby('GEMEINDE_NAME').size(),
                'PDF_Haushalte_Summe': pdf_data.groupby('Gemeinde')['Haushalte'].sum(),
                'PDF_Haushalte_Durchschnitt': pdf_data.groupby('Gemeinde')['Haushalte'].mean(),
                'PDF_Mietquote': (
                    pdf_data.groupby('Gemeinde')['Haushalte_zur_Miete'].sum() / 
                    pdf_data.groupby('Gemeinde')['Haushalte'].sum() * 100
                ).round(1)
            })
            
            logger.info("\nVergleich der Datensatzanzahl und Kennzahlen:")
            logger.info(comparison.to_string())
            
            # Speichere den Vergleich
            comparison.to_sql('data_comparison', self.conn, if_exists='replace')
            
            # Erstelle eine Zusammenfassung der Datenqualität
            quality_summary = pd.DataFrame({
                'PDF_Vollständigkeit': pdf_data.count() / len(pdf_data) * 100,
                'Excel_Vollständigkeit': excel_data.count() / len(excel_data) * 100
            }).round(1)
            
            logger.info("\nDatenqualität (Prozent der gefüllten Werte):")
            logger.info(quality_summary.to_string())
            
            # Speichere die Qualitätszusammenfassung
            quality_summary.to_sql('quality_summary', self.conn, if_exists='replace')
            
            logger.info("\nDaten erfolgreich zusammengeführt und analysiert")
            
        except Exception as e:
            logger.error(f"Fehler beim Zusammenführen der Daten: {str(e)}", exc_info=True)
    
    def verify_import(self):
        """Überprüft die importierten Daten"""
        logger.info("\nÜBERPRÜFE IMPORTIERTE DATEN:")
        
        try:
            cursor = self.conn.cursor()
            
            # Prüfe Wohnquartier-Daten
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(DISTINCT Gemeinde) as unique_cities,
                    COUNT(CASE WHEN Haushalte IS NOT NULL THEN 1 END) as with_households,
                    COUNT(CASE WHEN Haushalte_zur_Miete IS NOT NULL THEN 1 END) as with_rental,
                    COUNT(CASE WHEN Haushalte_mit_Kindern IS NOT NULL THEN 1 END) as with_children
                FROM wohnquartier
            """)
            stats = cursor.fetchone()
            logger.info(f"\nWohnquartier-Tabelle:")
            logger.info(f"  Gesamtanzahl Einträge: {stats[0]}")
            logger.info(f"  Eindeutige Städte: {stats[1]}")
            logger.info(f"  Mit Haushaltsdaten: {stats[2]} ({stats[2]/stats[0]*100:.1f}%)")
            logger.info(f"  Mit Mietdaten: {stats[3]} ({stats[3]/stats[0]*100:.1f}%)")
            logger.info(f"  Mit Kinderdaten: {stats[4]} ({stats[4]/stats[0]*100:.1f}%)")
            
            # Zeige Details pro Stadt
            cursor.execute("""
                SELECT 
                    Gemeinde,
                    COUNT(*) as total,
                    SUM(Haushalte) as total_households,
                    AVG(Haushalte) as avg_households,
                    MIN(Haushalte) as min_households,
                    MAX(Haushalte) as max_households,
                    COUNT(CASE WHEN Haushalte_zur_Miete IS NOT NULL THEN 1 END) as rental_count,
                    COUNT(CASE WHEN Haushalte_mit_Kindern IS NOT NULL THEN 1 END) as children_count,
                    ROUND(AVG(CASE WHEN Haushalte_zur_Miete IS NOT NULL 
                        THEN CAST(Haushalte_zur_Miete AS FLOAT) / CAST(Haushalte AS FLOAT) * 100 
                        ELSE NULL END), 1) as avg_rental_percentage
                FROM wohnquartier
                GROUP BY Gemeinde
            """)
            logger.info("\nDetails pro Stadt:")
            for row in cursor.fetchall():
                logger.info(f"  {row[0]}:")
                logger.info(f"    Anzahl Datensätze: {row[1]}")
                logger.info(f"    Gesamtzahl Haushalte: {row[2]}")
                logger.info(f"    Durchschnitt Haushalte: {row[3]:.1f}")
                logger.info(f"    Min/Max Haushalte: {row[4]}/{row[5]}")
                logger.info(f"    Datensätze mit Mietdaten: {row[6]} ({row[6]/row[1]*100:.1f}%)")
                logger.info(f"    Datensätze mit Kinderdaten: {row[7]} ({row[7]/row[1]*100:.1f}%)")
                if row[8] is not None:
                    logger.info(f"    Durchschnittliche Mietquote: {row[8]:.1f}%")
            
            # Prüfe Excel-Daten
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(DISTINCT WOHNQUART_SCHLUESSEL) as unique_keys,
                    COUNT(DISTINCT GEMEINDE_NAME) as unique_cities,
                    COUNT(CASE WHEN MOBILISIERUNGSINDEX_KLASSE_WKR IS NOT NULL THEN 1 END) as with_mobil,
                    COUNT(CASE WHEN UEBERZEUGUNSINDEX_KLASSE_WKR IS NOT NULL THEN 1 END) as with_ueberzeugung
                FROM excel_data
            """)
            stats = cursor.fetchone()
            logger.info(f"\nExcel-Tabelle:")
            logger.info(f"  Gesamtanzahl Einträge: {stats[0]}")
            logger.info(f"  Eindeutige Schlüssel: {stats[1]}")
            logger.info(f"  Eindeutige Städte: {stats[2]}")
            logger.info(f"  Mit Mobilisierungsindex: {stats[3]} ({stats[3]/stats[0]*100:.1f}%)")
            logger.info(f"  Mit Überzeugungsindex: {stats[4]} ({stats[4]/stats[0]*100:.1f}%)")
            
            # Zeige Details pro Stadt
            cursor.execute("""
                SELECT 
                    GEMEINDE_NAME,
                    COUNT(*) as total,
                    COUNT(DISTINCT WOHNQUART_SCHLUESSEL) as unique_quarters,
                    AVG(MOBILISIERUNGSINDEX_KLASSE_WKR) as avg_mobil,
                    MIN(MOBILISIERUNGSINDEX_KLASSE_WKR) as min_mobil,
                    MAX(MOBILISIERUNGSINDEX_KLASSE_WKR) as max_mobil,
                    AVG(UEBERZEUGUNSINDEX_KLASSE_WKR) as avg_ueberzeugung,
                    MIN(UEBERZEUGUNSINDEX_KLASSE_WKR) as min_ueberzeugung,
                    MAX(UEBERZEUGUNSINDEX_KLASSE_WKR) as max_ueberzeugung
                FROM excel_data
                GROUP BY GEMEINDE_NAME
            """)
            logger.info("\nDetails pro Stadt (Excel):")
            for row in cursor.fetchall():
                logger.info(f"  {row[0]}:")
                logger.info(f"    Anzahl Datensätze: {row[1]}")
                logger.info(f"    Eindeutige Wohnquartiere: {row[2]}")
                logger.info(f"    Mobilisierungsindex: Ø {row[3]:.2f} (Min: {row[4]}, Max: {row[5]})")
                logger.info(f"    Überzeugungsindex: Ø {row[6]:.2f} (Min: {row[7]}, Max: {row[8]})")
            
        except Exception as e:
            logger.error(f"Fehler bei der Überprüfung: {str(e)}", exc_info=True)
    
    def execute_import(self):
        """Führt den gesamten Import-Prozess durch"""
        self.connect_db()
        
        pdf_data = self.import_pdf()
        excel_data = self.import_excel()
        
        if pdf_data is not None or excel_data is not None:
            self.verify_import()
            self.merge_data()
        
        self.conn.commit()
        logger.info("\nImport abgeschlossen")
        self.conn.close()

def main():
    importer = DataImporter(
        pdf_path='/Users/winzendwyers/daten.pdf',
        excel_path='/Users/winzendwyers/daten.xlsx',
        db_path='neue_daten.db'
    )
    importer.execute_import()

if __name__ == "__main__":
    main() 