#!/usr/bin/env python3
"""
Script simple pour migrer les villes de MongoDB vers PostgreSQL/Supabase
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import psycopg2
from psycopg2.extras import execute_values
import certifi
import re

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

# Configuration MongoDB
MONGODB_URI = os.getenv('MONGODB_URI')
DB_NAME = os.getenv('DB_NAME', 'travliaq_knowledge_base')
CITY_COLLECTION = os.getenv('CITY_COLLECTION', 'cities')

# Configuration PostgreSQL/Supabase
PG_HOST = os.getenv('PG_HOST')
PG_DATABASE = os.getenv('PG_DATABASE', 'postgres')
PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_PORT = os.getenv('PG_PORT', '5432')
PG_SSLMODE = os.getenv('PG_SSLMODE', 'require')


def create_slug(name: str) -> str:
    """Crée un slug à partir du nom de la ville"""
    slug = name.lower()
    # Remplacer les espaces et caractères spéciaux par des tirets
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')


def connect_mongodb():
    """Connexion à MongoDB"""
    try:
        client = MongoClient(
            MONGODB_URI,
            tlsCAFile=certifi.where(),
            tls=True,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000
        )
        # Vérifier la connexion
        client.admin.command('ping')
        db = client[DB_NAME]
        logger.info("✓ Connexion MongoDB réussie")
        return client, db
    except Exception as e:
        logger.error(f"✗ Erreur de connexion MongoDB: {e}")
        raise


def connect_postgres():
    """Connexion à PostgreSQL/Supabase"""
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD,
            port=PG_PORT,
            sslmode=PG_SSLMODE
        )
        logger.info("✓ Connexion PostgreSQL réussie")
        return conn
    except Exception as e:
        logger.error(f"✗ Erreur de connexion PostgreSQL: {e}")
        raise


def migrate_cities():
    """Migration des villes de MongoDB vers PostgreSQL"""

    # Connexion aux bases de données
    mongo_client, mongo_db = connect_mongodb()
    pg_conn = connect_postgres()

    try:
        # Récupérer toutes les villes depuis MongoDB
        cities_collection = mongo_db[CITY_COLLECTION]
        cities = list(cities_collection.find())
        logger.info(f"📊 {len(cities)} villes trouvées dans MongoDB")

        if not cities:
            logger.warning("Aucune ville à migrer")
            return

        # Préparer les données pour l'insertion
        cities_data = []
        skipped = 0

        for city in cities:
            try:
                name = city.get('name')
                country_code = city.get('country_code')
                country_name = city.get('country_name')

                if not name or not country_code:
                    logger.warning(f"⚠ Ville ignorée (manque name ou country_code): {city.get('_id')}")
                    skipped += 1
                    continue

                # Créer le slug
                slug = create_slug(name)

                # Extraire les données
                latitude = city.get('latitude')
                longitude = city.get('longitude')
                state_code = city.get('state_code')
                state_name = city.get('state_name')
                population = city.get('population')

                # Créer le point géographique si latitude et longitude existent
                location = None
                if latitude is not None and longitude is not None:
                    # PostGIS format: POINT(longitude latitude)
                    # Note: PostGIS utilise (longitude, latitude) pas (latitude, longitude)
                    location = f'POINT({longitude} {latitude})'

                cities_data.append({
                    'name': name,
                    'country': country_name or '',
                    'country_code': country_code,
                    'slug': slug,
                    'latitude': latitude,
                    'longitude': longitude,
                    'location': location,
                    'state_code': state_code,
                    'state_name': state_name,
                    'population': population
                })

            except Exception as e:
                logger.error(f"✗ Erreur lors du traitement de la ville {city.get('name', 'inconnu')}: {e}")
                skipped += 1
                continue

        logger.info(f"📝 {len(cities_data)} villes prêtes pour l'insertion, {skipped} ignorées")

        if not cities_data:
            logger.warning("Aucune ville valide à insérer")
            return

        # Insertion dans PostgreSQL avec UPSERT
        cursor = pg_conn.cursor()

        # UPSERT basé sur la contrainte unique (slug, country_code)
        insert_query = """
            INSERT INTO public.cities (
                name, country, country_code, slug,
                latitude, longitude, location,
                state_code, state_name, population,
                updated_at
            )
            VALUES %s
            ON CONFLICT (slug, country_code)
            DO UPDATE SET
                name = EXCLUDED.name,
                country = EXCLUDED.country,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                location = EXCLUDED.location,
                state_code = EXCLUDED.state_code,
                state_name = EXCLUDED.state_name,
                population = EXCLUDED.population,
                updated_at = EXCLUDED.updated_at
        """

        # Préparer les valeurs
        values = []
        for c in cities_data:
            # Si location existe, utiliser ST_GeogFromText pour créer la géographie
            if c['location']:
                values.append((
                    c['name'],
                    c['country'],
                    c['country_code'],
                    c['slug'],
                    c['latitude'],
                    c['longitude'],
                    f"SRID=4326;{c['location']}",  # WGS84 SRID
                    c['state_code'],
                    c['state_name'],
                    c['population'],
                    datetime.now()
                ))
            else:
                values.append((
                    c['name'],
                    c['country'],
                    c['country_code'],
                    c['slug'],
                    c['latitude'],
                    c['longitude'],
                    None,
                    c['state_code'],
                    c['state_name'],
                    c['population'],
                    datetime.now()
                ))

        # Exécuter l'insertion en batch
        execute_values(cursor, insert_query, values)
        pg_conn.commit()

        logger.info(f"✓ {len(cities_data)} villes insérées/mises à jour dans PostgreSQL")

        # Vérification
        cursor.execute("SELECT COUNT(*) FROM public.cities")
        total_cities = cursor.fetchone()[0]
        logger.info(f"📊 Total de villes dans PostgreSQL: {total_cities}")

        # Afficher quelques exemples
        cursor.execute("""
            SELECT name, country, country_code, slug, latitude, longitude
            FROM public.cities
            ORDER BY name
            LIMIT 5
        """)
        examples = cursor.fetchall()
        logger.info("📍 Exemples de villes migrées:")
        for ex in examples:
            logger.info(f"   - {ex[0]}, {ex[1]} ({ex[2]}) → slug: {ex[3]}")

        cursor.close()

    except Exception as e:
        logger.error(f"✗ Erreur pendant la migration: {e}")
        pg_conn.rollback()
        raise

    finally:
        # Fermer les connexions
        if mongo_client:
            mongo_client.close()
            logger.info("✓ Connexion MongoDB fermée")

        if pg_conn:
            pg_conn.close()
            logger.info("✓ Connexion PostgreSQL fermée")


def main():
    """Point d'entrée principal"""
    logger.info("=" * 60)
    logger.info("🚀 Démarrage de la migration des villes MongoDB → PostgreSQL")
    logger.info("=" * 60)

    # Vérifier les variables d'environnement MongoDB
    if not MONGODB_URI:
        logger.error("✗ MONGODB_URI non défini dans le fichier .env")
        return

    # Vérifier les variables d'environnement PostgreSQL
    missing_vars = []
    if not PG_HOST:
        missing_vars.append("PG_HOST")
    if not PG_USER:
        missing_vars.append("PG_USER")
    if not PG_PASSWORD:
        missing_vars.append("PG_PASSWORD")

    if missing_vars:
        logger.error(f"✗ Variables PostgreSQL manquantes dans le fichier .env: {', '.join(missing_vars)}")
        return

    try:
        migrate_cities()
        logger.info("=" * 60)
        logger.info("✅ Migration des villes terminée avec succès!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ Échec de la migration: {e}")
        logger.error("=" * 60)
        raise


if __name__ == "__main__":
    main()
