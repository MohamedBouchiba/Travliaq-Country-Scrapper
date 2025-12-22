#!/usr/bin/env python3
"""
Script pour migrer à la fois les pays ET les villes de MongoDB vers PostgreSQL/Supabase
"""

import logging
from migrate_to_postgres import migrate_countries
from migrate_cities_to_postgres import migrate_cities

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Migrer tous les données: pays et villes"""

    logger.info("🌍" * 30)
    logger.info("🚀 Migration complète MongoDB → PostgreSQL")
    logger.info("🌍" * 30)
    print()

    try:
        # 1. Migrer les pays d'abord
        logger.info("🏳️  Étape 1/2: Migration des pays...")
        print()
        migrate_countries()
        print()

        # 2. Ensuite migrer les villes
        logger.info("🏙️  Étape 2/2: Migration des villes...")
        print()
        migrate_cities()
        print()

        # Résumé final
        logger.info("=" * 60)
        logger.info("✅ Migration complète terminée avec succès!")
        logger.info("   ✓ Pays migrés")
        logger.info("   ✓ Villes migrées")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ Échec de la migration: {e}")
        logger.error("=" * 60)
        raise


if __name__ == "__main__":
    main()
