#!/usr/bin/env python3
"""
Script raccourci pour lancer la migration depuis la racine
Usage:
    python migrate.py test         # Tester les connexions
    python migrate.py countries    # Migrer uniquement les pays
    python migrate.py cities       # Migrer uniquement les villes
    python migrate.py all          # Migrer tout (par défaut)
"""

import sys
import os

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(__file__))

from src.migration.test_connection import main as test_main
from src.migration.migrate_to_postgres import main as countries_main
from src.migration.migrate_cities_to_postgres import main as cities_main
from src.migration.migrate_all import main as all_main


def print_usage():
    """Afficher l'aide"""
    print("Usage: python migrate.py [command]")
    print()
    print("Commands:")
    print("  test        Tester les connexions aux bases de données")
    print("  countries   Migrer uniquement les pays")
    print("  cities      Migrer uniquement les villes")
    print("  all         Migrer tout (pays + villes) [par défaut]")
    print()


if __name__ == "__main__":
    # Récupérer la commande
    command = sys.argv[1] if len(sys.argv) > 1 else "all"

    if command == "test":
        test_main()
    elif command == "countries":
        countries_main()
    elif command == "cities":
        cities_main()
    elif command == "all":
        all_main()
    elif command in ["--help", "-h", "help"]:
        print_usage()
    else:
        print(f"❌ Commande inconnue: {command}")
        print()
        print_usage()
        sys.exit(1)
