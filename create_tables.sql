-- Erstelle die Tabellen

-- Route Tabelle
CREATE TABLE IF NOT EXISTS routes (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    street VARCHAR(100) NOT NULL,
    house_numbers VARCHAR(100) NOT NULL,
    zip_code VARCHAR(5),
    district VARCHAR(100),
    mobilization_index INTEGER,
    conviction_index INTEGER,
    households INTEGER,
    rental_percentage FLOAT,
    lat FLOAT,
    lon FLOAT,
    meeting_point VARCHAR(200),
    meeting_point_lat FLOAT,
    meeting_point_lon FLOAT,
    max_volunteers INTEGER DEFAULT 4,
    is_active BOOLEAN DEFAULT TRUE,
    path_coordinates JSONB,
    needs_review BOOLEAN DEFAULT FALSE
);

-- Volunteer Tabelle
CREATE TABLE IF NOT EXISTS volunteers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20)
);

-- RouteRegistration Tabelle
CREATE TABLE IF NOT EXISTS route_registrations (
    id SERIAL PRIMARY KEY,
    volunteer_id INTEGER REFERENCES volunteers(id),
    route_id INTEGER REFERENCES routes(id),
    date DATE NOT NULL,
    time_slot VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'geplant',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User Tabelle
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(200) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE
);

-- Erstelle Indizes für bessere Performance
CREATE INDEX IF NOT EXISTS idx_routes_city ON routes(city);
CREATE INDEX IF NOT EXISTS idx_routes_district ON routes(district);
CREATE INDEX IF NOT EXISTS idx_volunteers_email ON volunteers(email);
CREATE INDEX IF NOT EXISTS idx_registrations_route ON route_registrations(route_id);
CREATE INDEX IF NOT EXISTS idx_registrations_volunteer ON route_registrations(volunteer_id);
CREATE INDEX IF NOT EXISTS idx_registrations_date ON route_registrations(date); 