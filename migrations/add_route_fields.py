"""Add zip_code and path_coordinates to routes

Revision ID: add_route_fields
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Füge die neuen Spalten hinzu
    op.add_column('route', sa.Column('zip_code', sa.String(5), nullable=True))
    op.add_column('route', sa.Column('path_coordinates', sa.JSON, nullable=True))
    
    # Aktualisiere bestehende Routen mit Postleitzahlen
    op.execute("""
        UPDATE route 
        SET zip_code = CASE
            WHEN city = 'Moers' THEN '47441'
            WHEN city = 'Krefeld' THEN '47798'
            WHEN city = 'Neukirchen-Vluyn' THEN '47506'
            ELSE NULL
        END
    """)

def downgrade():
    op.drop_column('route', 'zip_code')
    op.drop_column('route', 'path_coordinates') 