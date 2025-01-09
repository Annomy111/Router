-- Aktiviere Row Level Security (RLS)
ALTER TABLE routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE volunteers ENABLE ROW LEVEL SECURITY;
ALTER TABLE route_registrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Policies für routes
CREATE POLICY "Öffentlicher Lesezugriff auf Routen"
    ON routes FOR SELECT
    TO anon
    USING (true);

-- Policies für volunteers
CREATE POLICY "Freiwillige können sich selbst registrieren"
    ON volunteers FOR INSERT
    TO anon
    WITH CHECK (true);

CREATE POLICY "Freiwillige können ihre eigenen Daten sehen"
    ON volunteers FOR SELECT
    TO anon
    USING (true);

-- Policies für route_registrations
CREATE POLICY "Freiwillige können Registrierungen erstellen"
    ON route_registrations FOR INSERT
    TO anon
    WITH CHECK (true);

CREATE POLICY "Öffentlicher Lesezugriff auf Registrierungen"
    ON route_registrations FOR SELECT
    TO anon
    USING (true);

-- Policies für users
CREATE POLICY "Nur Admins können User verwalten"
    ON users FOR ALL
    TO authenticated
    USING (is_admin = true)
    WITH CHECK (is_admin = true); 