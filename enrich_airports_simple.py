"""
Script simplifié pour enrichir la table airports avec les métadonnées d'OurAirports.
Version sans pandas pour éviter les problèmes de dépendances.
"""

import os
import sys
import logging
from dotenv import load_dotenv
import psycopg2
import requests
import csv
from io import StringIO

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

PG_HOST = os.getenv('PG_HOST')
PG_DATABASE = os.getenv('PG_DATABASE', 'postgres')
PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_PORT = int(os.getenv('PG_PORT', 5432))
PG_SSLMODE = os.getenv('PG_SSLMODE', 'require')

OURAIRPORTS_URL = 'https://davidmegginson.github.io/ourairports-data/airports.csv'


def download_ourairports():
    """Télécharge les données OurAirports."""
    logger.info("Downloading OurAirports data...")

    try:
        response = requests.get(OURAIRPORTS_URL, timeout=30)
        response.raise_for_status()

        # Parser le CSV
        reader = csv.DictReader(StringIO(response.text))

        airports = {}
        for row in reader:
            iata = row.get('iata_code', '').strip()
            if iata and len(iata) == 3:
                airports[iata] = {
                    'type': row.get('type', ''),
                    'scheduled_service': row.get('scheduled_service', '')
                }

        logger.info(f"Downloaded {len(airports)} airports with valid IATA codes")
        return airports

    except Exception as e:
        logger.error(f"Failed to download OurAirports data: {e}")
        raise


def connect_db():
    """Connexion à PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD,
            port=PG_PORT,
            sslmode=PG_SSLMODE
        )
        logger.info("Connected to PostgreSQL successfully")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise


def add_metadata_columns(conn):
    """Ajoute les colonnes de métadonnées si elles n'existent pas."""
    cursor = conn.cursor()

    try:
        # Vérifier si les colonnes existent déjà
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'airports'
              AND column_name IN ('airport_type', 'scheduled_service')
        """)

        existing_columns = {row[0] for row in cursor.fetchall()}

        # Ajouter airport_type si elle n'existe pas
        if 'airport_type' not in existing_columns:
            logger.info("Adding column 'airport_type' to airports table...")
            cursor.execute("""
                ALTER TABLE airports
                ADD COLUMN airport_type VARCHAR(50)
            """)
            logger.info("Column 'airport_type' added successfully")
        else:
            logger.info("Column 'airport_type' already exists")

        # Ajouter scheduled_service si elle n'existe pas
        if 'scheduled_service' not in existing_columns:
            logger.info("Adding column 'scheduled_service' to airports table...")
            cursor.execute("""
                ALTER TABLE airports
                ADD COLUMN scheduled_service VARCHAR(10)
            """)
            logger.info("Column 'scheduled_service' added successfully")
        else:
            logger.info("Column 'scheduled_service' already exists")

        conn.commit()
        cursor.close()

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to add columns: {e}")
        raise


def update_airport_metadata(conn, ourairports_data):
    """Met à jour les métadonnées des aéroports."""
    cursor = conn.cursor()

    try:
        logger.info("Updating airport metadata...")

        updated_count = 0
        not_found_count = 0

        for iata, metadata in ourairports_data.items():
            # Mettre à jour l'aéroport
            cursor.execute("""
                UPDATE airports
                SET airport_type = %s,
                    scheduled_service = %s
                WHERE iata = %s
            """, (metadata['type'], metadata['scheduled_service'], iata))

            if cursor.rowcount > 0:
                updated_count += 1
            else:
                not_found_count += 1

        conn.commit()

        logger.info(f"Updated {updated_count} airports")
        logger.info(f"Not found in DB: {not_found_count} airports")

        cursor.close()

        return updated_count

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update metadata: {e}")
        raise


def create_commercial_airports_view(conn):
    """Crée la vue commercial_airports."""
    cursor = conn.cursor()

    try:
        logger.info("Creating/replacing 'commercial_airports' view...")

        cursor.execute("""
            CREATE OR REPLACE VIEW commercial_airports AS
            SELECT
                iata,
                name,
                country_code,
                location,
                airport_type,
                scheduled_service
            FROM airports
            WHERE
                -- Aéroports commerciaux avec code IATA valide
                iata IS NOT NULL
                AND LENGTH(iata) = 3
                AND (
                    -- Large ou medium airports (toujours commerciaux)
                    airport_type IN ('large_airport', 'medium_airport')

                    -- OU small airports avec service programmé
                    OR (
                        airport_type = 'small_airport'
                        AND scheduled_service = 'yes'
                    )
                )
                -- Exclure les types non-commerciaux
                AND airport_type NOT IN (
                    'heliport',
                    'seaplane_base',
                    'closed',
                    'balloonport'
                )
                -- Exclure les noms avec keywords militaires/privés
                AND name NOT ILIKE '%RAF%'
                AND name NOT ILIKE '%Air Force%'
                AND name NOT ILIKE '%Military%'
                AND name NOT ILIKE '%Naval%'
                AND name NOT ILIKE '%Navy%'
                AND name NOT ILIKE '%Army%'
                AND name NOT ILIKE '%Air Base%'
                AND name NOT ILIKE '%Airbase%'
                AND name NOT ILIKE '%Camp%'
                AND name NOT ILIKE '%Heliport%'
                AND name NOT ILIKE '%Executive%'
                AND name NOT ILIKE '%Le Bourget%'
                AND name NOT ILIKE '%Toussus%'
                AND name NOT ILIKE '%Pontoise%'
        """)

        conn.commit()

        logger.info("View 'commercial_airports' created successfully")

        # Compter les aéroports dans la vue
        cursor.execute("SELECT COUNT(*) FROM commercial_airports")
        count = cursor.fetchone()[0]
        logger.info(f"View contains {count} commercial airports")

        cursor.close()

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to create view: {e}")
        raise


def show_statistics(conn):
    """Affiche les statistiques."""
    cursor = conn.cursor()

    logger.info("\n" + "=" * 80)
    logger.info("STATISTICS")
    logger.info("=" * 80)

    # Total aéroports
    cursor.execute("SELECT COUNT(*) FROM airports WHERE iata IS NOT NULL AND LENGTH(iata) = 3")
    total = cursor.fetchone()[0]

    # Aéroports avec métadonnées
    cursor.execute("""
        SELECT COUNT(*) FROM airports
        WHERE iata IS NOT NULL
          AND LENGTH(iata) = 3
          AND airport_type IS NOT NULL
    """)
    with_metadata = cursor.fetchone()[0]

    # Aéroports commerciaux
    cursor.execute("SELECT COUNT(*) FROM commercial_airports")
    commercial = cursor.fetchone()[0]

    # Par type
    cursor.execute("""
        SELECT airport_type, COUNT(*) as count
        FROM airports
        WHERE iata IS NOT NULL
          AND LENGTH(iata) = 3
          AND airport_type IS NOT NULL
        GROUP BY airport_type
        ORDER BY count DESC
    """)
    types = cursor.fetchall()

    logger.info(f"\nTotal airports (with IATA):        {total}")
    logger.info(f"Airports with metadata:            {with_metadata} ({with_metadata/total*100:.1f}%)")
    logger.info(f"Commercial airports (in view):     {commercial} ({commercial/total*100:.1f}%)")
    logger.info(f"Non-commercial (filtered out):     {total - commercial} ({(total-commercial)/total*100:.1f}%)")

    logger.info("\nBreakdown by type:")
    for airport_type, count in types:
        logger.info(f"  - {airport_type:<20}: {count:>5}")

    logger.info("")
    cursor.close()


def main():
    """Script principal."""
    logger.info("=" * 80)
    logger.info("AIRPORT METADATA ENRICHMENT (Simplified)")
    logger.info("=" * 80)
    logger.info("")

    # Vérifier la configuration PostgreSQL
    if not all([PG_HOST, PG_USER, PG_PASSWORD]):
        logger.error("PostgreSQL configuration missing. Please check your .env file.")
        sys.exit(1)

    try:
        # 1. Télécharger OurAirports
        ourairports_data = download_ourairports()

        # 2. Se connecter à PostgreSQL
        conn = connect_db()

        # 3. Ajouter les colonnes de métadonnées
        add_metadata_columns(conn)

        # 4. Mettre à jour les métadonnées
        update_airport_metadata(conn, ourairports_data)

        # 5. Créer la vue commercial_airports
        create_commercial_airports_view(conn)

        # 6. Afficher les statistiques
        show_statistics(conn)

        # Fermer la connexion
        conn.close()

        logger.info("=" * 80)
        logger.info("SUCCESS: Airport metadata enrichment completed!")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Update app/services/airports.py to use 'commercial_airports' view")
        logger.info("2. Test the /nearest-airports endpoint")
        logger.info("3. Verify that only commercial airports are returned")
        logger.info("")

    except Exception as e:
        logger.error(f"Script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
