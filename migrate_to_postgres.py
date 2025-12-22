#!/usr/bin/env python3
"""
Script simple pour migrer les données de MongoDB vers PostgreSQL/Supabase
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
COUNTRY_COLLECTION = os.getenv('COUNTRY_COLLECTION', 'countries')

# Configuration PostgreSQL/Supabase
PG_HOST = os.getenv('PG_HOST')
PG_DATABASE = os.getenv('PG_DATABASE', 'postgres')
PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_PORT = os.getenv('PG_PORT', '5432')
PG_SSLMODE = os.getenv('PG_SSLMODE', 'require')


def create_slug(name: str) -> str:
    """Crée un slug à partir du nom du pays"""
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


def migrate_countries():
    """Migration des pays de MongoDB vers PostgreSQL"""

    # Connexion aux bases de données
    mongo_client, mongo_db = connect_mongodb()
    pg_conn = connect_postgres()

    try:
        # Récupérer tous les pays depuis MongoDB
        countries_collection = mongo_db[COUNTRY_COLLECTION]
        countries = list(countries_collection.find())
        logger.info(f"📊 {len(countries)} pays trouvés dans MongoDB")

        if not countries:
            logger.warning("Aucun pays à migrer")
            return

        # Préparer les données pour l'insertion
        countries_data = []
        skipped = 0

        for country in countries:
            try:
                iso2 = country.get('code_iso2')
                iso3 = country.get('code_iso3')
                name = country.get('name')

                if not iso2 or not name:
                    logger.warning(f"⚠ Pays ignoré (manque iso2 ou name): {country.get('_id')}")
                    skipped += 1
                    continue

                # Créer le slug
                slug = create_slug(name)

                # Extraire les données
                population = country.get('population')
                region = country.get('region')
                subregion = country.get('subregion')

                countries_data.append({
                    'iso2': iso2,
                    'iso3': iso3,
                    'name': name,
                    'slug': slug,
                    'population': population,
                    'region': region,
                    'subregion': subregion
                })

            except Exception as e:
                logger.error(f"✗ Erreur lors du traitement du pays {country.get('name', 'inconnu')}: {e}")
                skipped += 1
                continue

        logger.info(f"📝 {len(countries_data)} pays prêts pour l'insertion, {skipped} ignorés")

        # Insertion dans PostgreSQL avec UPSERT
        cursor = pg_conn.cursor()

        insert_query = """
            INSERT INTO public.countries (iso2, iso3, name, slug, population, region, subregion, updated_at)
            VALUES %s
            ON CONFLICT (iso2)
            DO UPDATE SET
                iso3 = EXCLUDED.iso3,
                name = EXCLUDED.name,
                slug = EXCLUDED.slug,
                population = EXCLUDED.population,
                region = EXCLUDED.region,
                subregion = EXCLUDED.subregion,
                updated_at = EXCLUDED.updated_at
        """

        # Préparer les valeurs
        values = [
            (
                c['iso2'],
                c['iso3'],
                c['name'],
                c['slug'],
                c['population'],
                c['region'],
                c['subregion'],
                datetime.now()
            )
            for c in countries_data
        ]

        # Exécuter l'insertion en batch
        execute_values(cursor, insert_query, values)
        pg_conn.commit()

        logger.info(f"✓ {len(countries_data)} pays insérés/mis à jour dans PostgreSQL")

        # Vérification
        cursor.execute("SELECT COUNT(*) FROM public.countries")
        total_countries = cursor.fetchone()[0]
        logger.info(f"📊 Total de pays dans PostgreSQL: {total_countries}")

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
    logger.info("🚀 Démarrage de la migration MongoDB → PostgreSQL")
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
        migrate_countries()
        logger.info("=" * 60)
        logger.info("✅ Migration terminée avec succès!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ Échec de la migration: {e}")
        logger.error("=" * 60)
        raise


if __name__ == "__main__":
    main()
