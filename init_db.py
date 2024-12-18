from app import app, db, Route

def init_db():
    with app.app_context():
        print("Initialisiere Datenbank...")
        # Erstelle alle Tabellen
        db.create_all()
        print("Tabellen wurden erstellt")
        
        # Prüfe ob Routen existieren
        if Route.query.count() == 0:
            print("Füge initiale Routen hinzu...")
            routes = [
                Route(
                    city='Moers',
                    street='Niephauser Straße',
                    house_numbers='81-165',
                    mobilization_index=3,
                    conviction_index=3,
                    households=None,
                    rental_percentage=None,
                    lat=51.451,
                    lon=6.626
                ),
                Route(
                    city='Moers',
                    street='Windmühlenstraße',
                    house_numbers='59-99',
                    mobilization_index=3,
                    conviction_index=3,
                    households=None,
                    rental_percentage=None,
                    lat=51.449,
                    lon=6.623
                ),
                Route(
                    city='Krefeld',
                    street='Gubener Straße',
                    house_numbers='1-41',
                    mobilization_index=3,
                    conviction_index=3,
                    households=949,
                    rental_percentage=74.6,
                    lat=51.333,
                    lon=6.564
                ),
                Route(
                    city='Krefeld',
                    street='Breslauer Straße',
                    house_numbers='1-31',
                    mobilization_index=3,
                    conviction_index=3,
                    households=949,
                    rental_percentage=74.6,
                    lat=51.335,
                    lon=6.568
                )
            ]
            for route in routes:
                db.session.add(route)
            db.session.commit()
            print("Initiale Routen wurden hinzugefügt")
        else:
            print("Routen existieren bereits")
        
        print("Datenbankinitialisierung abgeschlossen")

if __name__ == "__main__":
    init_db() 