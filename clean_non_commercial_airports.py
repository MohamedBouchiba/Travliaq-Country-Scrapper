#!/usr/bin/env python3
"""
Script pour nettoyer les aéroports non-commerciaux de la base de données PostgreSQL.

Ce script utilise une validation multi-sources pour identifier et supprimer les aéroports
non-commerciaux (militaires, privés, heliports, etc.) tout en conservant les aéroports commerciaux.

Sources de validation:
1. OurAirports (primaire): CSV avec type d'aéroport et service programmé
2. OpenFlights (secondaire): Base de données d'aéroports commerciaux
3. Filtres de nom (tertiaire): Keywords pour détecter aéroports militaires/privés

Usage:
    # Mode dry-run (par défaut, ne supprime rien)
    python clean_non_commercial_airports.py --dry-run

    # Mode suppression réelle
    python clean_non_commercial_airports.py --delete

    # Forcer le téléchargement des sources
    python clean_non_commercial_airports.py --download-sources
"""

import os
import sys
import logging
import argparse
import requests
import pandas as pd
import psycopg2
from datetime import datetime
from io import StringIO
from typing import Tuple, List, Dict, Optional
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

# Configuration PostgreSQL
PG_HOST = os.getenv('PG_HOST')
PG_DATABASE = os.getenv('PG_DATABASE', 'postgres')
PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_PORT = os.getenv('PG_PORT', '5432')
PG_SSLMODE = os.getenv('PG_SSLMODE', 'require')

# URLs des sources externes
OURAIRPORTS_URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
OPENFLIGHTS_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"

# Keywords pour filtrer les aéroports non-commerciaux
NON_COMMERCIAL_KEYWORDS = [
    'RAF', 'Air Force', 'Military', 'Naval', 'Navy', 'Army',
    'Air Base', 'Airbase', 'Camp', 'Base', 'Airstrip',
    'Aerodrome', 'Aérodrome', 'Heliport', 'Field',
    'Executive', 'Biggin Hill'
]

# Liste des aéroports incertains à forcer la suppression
# (militaires, non-commerciaux, fermés/historiques identifiés manuellement)
UNCERTAIN_AIRPORTS_TO_DELETE = [
    'AEI', 'AGQ', 'AVR', 'BGZ', 'BXP', 'DOK', 'DSA', 'ETH', 'FBU', 'FEL',
    'FSS', 'FZO', 'GUT', 'GZA', 'HDI', 'HEM', 'HRT', 'ISN', 'KRH', 'LID',
    'LYE', 'MPK', 'MZM', 'NGZ', 'NHA', 'NSY', 'NXX', 'OSP', 'QFO', 'QKX',
    'QLP', 'QLR', 'QLT', 'QQT', 'QUY', 'QYD', 'RHE', 'SQZ', 'SXF', 'THF',
    'TXL', 'TZR', 'UTC', 'WSD', 'XOG', 'XXN', 'YXD', 'ZIN', 'ZNF'
]


def safe_print(text: str):
    """
    Affiche du texte en gérant les erreurs d'encodage Unicode pour Windows.
    Remplace les caractères problématiques par leur équivalent ASCII.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        # Remplacer les caractères non-ASCII par leur équivalent
        ascii_text = text.encode('ascii', errors='replace').decode('ascii')
        print(ascii_text)


class AirportValidator:
    """Classe pour valider si un aéroport est commercial via sources multiples."""

    def __init__(self):
        self.ourairports_df = None
        self.openflights_df = None
        self.cache_dir = os.path.join(os.path.dirname(__file__), '.cache')
        os.makedirs(self.cache_dir, exist_ok=True)

    def download_ourairports(self, force=False) -> pd.DataFrame:
        """
        Télécharge et parse les données OurAirports.

        Args:
            force: Force le téléchargement même si un cache existe

        Returns:
            DataFrame avec colonnes: iata_code, type, name, scheduled_service
        """
        cache_file = os.path.join(self.cache_dir, 'ourairports.csv')

        if not force and os.path.exists(cache_file):
            logger.info("Loading OurAirports from cache...")
            df = pd.read_csv(cache_file)
        else:
            logger.info(f"Downloading OurAirports data from {OURAIRPORTS_URL}...")
            try:
                response = requests.get(OURAIRPORTS_URL, timeout=30)
                response.raise_for_status()

                # Parse CSV
                df = pd.read_csv(StringIO(response.text))

                # Garder uniquement les colonnes utiles
                columns_to_keep = ['iata_code', 'type', 'name', 'scheduled_service']
                df = df[columns_to_keep]

                # Filtrer les lignes sans code IATA
                df = df[df['iata_code'].notna()]

                # Sauvegarder en cache
                df.to_csv(cache_file, index=False)
                logger.info(f"OurAirports data cached to {cache_file}")

            except Exception as e:
                logger.error(f"Failed to download OurAirports data: {e}")
                raise

        logger.info(f"Loaded {len(df)} airports from OurAirports")
        return df

    def download_openflights(self, force=False) -> pd.DataFrame:
        """
        Télécharge et parse les données OpenFlights.

        Args:
            force: Force le téléchargement même si un cache existe

        Returns:
            DataFrame avec colonnes: iata, name
        """
        cache_file = os.path.join(self.cache_dir, 'openflights.csv')

        if not force and os.path.exists(cache_file):
            logger.info("Loading OpenFlights from cache...")
            df = pd.read_csv(cache_file)
        else:
            logger.info(f"Downloading OpenFlights data from {OPENFLIGHTS_URL}...")
            try:
                response = requests.get(OPENFLIGHTS_URL, timeout=30)
                response.raise_for_status()

                # Parse CSV (pas de header, colonnes fixes)
                # Format: Airport ID, Name, City, Country, IATA, ICAO, Lat, Lon, Alt, Timezone, DST, Tz, Type, Source
                df = pd.read_csv(
                    StringIO(response.text),
                    header=None,
                    names=['id', 'name', 'city', 'country', 'iata', 'icao', 'lat', 'lon',
                           'altitude', 'timezone', 'dst', 'tz_database', 'type', 'source']
                )

                # Garder uniquement les colonnes utiles
                df = df[['iata', 'name']]

                # Filtrer les lignes sans code IATA ou avec \\N (null marker)
                df = df[(df['iata'].notna()) & (df['iata'] != '\\N')]

                # Sauvegarder en cache
                df.to_csv(cache_file, index=False)
                logger.info(f"OpenFlights data cached to {cache_file}")

            except Exception as e:
                logger.error(f"Failed to download OpenFlights data: {e}")
                raise

        logger.info(f"Loaded {len(df)} airports from OpenFlights")
        return df

    def load_sources(self, force_download=False):
        """Charge les sources de données externes."""
        logger.info("=" * 60)
        logger.info("Loading external data sources...")
        logger.info("=" * 60)

        self.ourairports_df = self.download_ourairports(force=force_download)
        self.openflights_df = self.download_openflights(force=force_download)

        logger.info("\nSources loaded successfully!")
        logger.info(f"  - OurAirports: {len(self.ourairports_df)} airports")
        logger.info(f"  - OpenFlights: {len(self.openflights_df)} airports")
        logger.info("")

    def validate_airport(self, iata_code: str, label: str) -> Tuple[Optional[bool], List[str], Dict[str, int]]:
        """
        Valide si un aéroport est commercial via système de points multi-sources.

        Système de points:
        - OurAirports large/medium: +2 commercial
        - OurAirports small avec service: +2 commercial
        - OurAirports small sans service: +2 non-commercial
        - OurAirports heliport/seaplane/closed: +2 non-commercial
        - OpenFlights présent: +1 commercial
        - Label contient keyword: +1 non-commercial

        Décision:
        - >= 2 points non-commercial: DELETE
        - >= 2 points commercial: KEEP
        - Sinon: KEEP (conservateur)

        Args:
            iata_code: Code IATA de l'aéroport
            label: Nom de l'aéroport

        Returns:
            Tuple (is_commercial, reasons, scores)
            - is_commercial: True (commercial), False (non-commercial), None (incertain)
            - reasons: Liste des raisons de validation
            - scores: Dict avec keys 'commercial' et 'non_commercial'
        """
        points_commercial = 0
        points_non_commercial = 0
        reasons = []

        # Source 1: OurAirports validation
        oa_match = self.ourairports_df[self.ourairports_df['iata_code'] == iata_code]

        if not oa_match.empty:
            airport_type = oa_match.iloc[0]['type']
            scheduled = str(oa_match.iloc[0]['scheduled_service']).lower()

            if airport_type in ['large_airport', 'medium_airport']:
                points_commercial += 2
                reasons.append(f"OurAirports: {airport_type}")

            elif airport_type == 'small_airport':
                if scheduled == 'yes':
                    points_commercial += 2
                    reasons.append("OurAirports: small airport with scheduled service")
                else:
                    points_non_commercial += 2
                    reasons.append("OurAirports: small airport without scheduled service")

            elif airport_type in ['heliport', 'seaplane_base', 'closed', 'balloonport']:
                points_non_commercial += 2
                reasons.append(f"OurAirports: {airport_type}")
            else:
                reasons.append(f"OurAirports: {airport_type} (unclassified)")
        else:
            reasons.append("OurAirports: not found")

        # Source 2: OpenFlights validation
        of_match = self.openflights_df[self.openflights_df['iata'] == iata_code]
        if not of_match.empty:
            points_commercial += 1
            reasons.append("OpenFlights: present")
        else:
            reasons.append("OpenFlights: not found")

        # Source 3: Label keyword filtering
        matched_keywords = []
        for keyword in NON_COMMERCIAL_KEYWORDS:
            if keyword.lower() in label.lower():
                matched_keywords.append(keyword)

        if matched_keywords:
            points_non_commercial += 1
            reasons.append(f"Label: contains {', '.join(matched_keywords)}")

        # Décision basée sur les points (validation stricte multi-sources)
        scores = {
            'commercial': points_commercial,
            'non_commercial': points_non_commercial
        }

        if points_non_commercial >= 2:
            # Confirmé non-commercial par au moins 2 sources
            return False, reasons, scores
        elif points_commercial >= 2:
            # Confirmé commercial par au moins 2 sources
            return True, reasons, scores
        else:
            # Incertain - garder par défaut (approche conservatrice)
            return None, reasons, scores


def connect_postgres() -> psycopg2.extensions.connection:
    """Connexion à PostgreSQL."""
    logger.info("Connecting to PostgreSQL...")
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
        logger.error(f"[ERROR] Failed to connect to PostgreSQL: {e}")
        raise


def fetch_airports_from_db(conn) -> List[Tuple[str, str, str]]:
    """
    Récupère tous les aéroports de la base de données.

    Returns:
        Liste de tuples (iata_code, label, country_code)
    """
    logger.info("Fetching airports from database...")

    cursor = conn.cursor()
    query = """
        SELECT ref, label, country_code
        FROM search_autocomplete
        WHERE type = 'airport'
          AND ref IS NOT NULL
          AND LENGTH(ref) = 3
        ORDER BY ref
    """

    cursor.execute(query)
    airports = cursor.fetchall()
    cursor.close()

    logger.info(f"Found {len(airports)} airports in database")
    return airports


def process_airports(validator: AirportValidator, airports: List[Tuple[str, str, str]]) -> Dict:
    """
    Traite tous les aéroports et génère les résultats de validation.

    Returns:
        Dict avec keys: 'keep', 'delete', 'review' (listes d'aéroports)
    """
    results = {
        'keep': [],
        'delete': [],
        'review': []
    }

    logger.info("\n" + "=" * 60)
    logger.info(f"Processing {len(airports)} airports...")
    logger.info("=" * 60 + "\n")

    for idx, (iata, label, country) in enumerate(airports, 1):
        is_commercial, reasons, scores = validator.validate_airport(iata, label)

        # Déterminer l'action
        if is_commercial is False:
            action = 'DELETE'
            status = '[X]'
            results['delete'].append({
                'iata': iata,
                'label': label,
                'country': country,
                'is_commercial': False,
                'scores': scores,
                'reasons': reasons
            })
        elif is_commercial is True:
            action = 'KEEP'
            status = '[OK]'
            results['keep'].append({
                'iata': iata,
                'label': label,
                'country': country,
                'is_commercial': True,
                'scores': scores,
                'reasons': reasons
            })
        else:
            # Aéroport incertain - vérifier s'il est dans la liste manuelle de suppression
            if iata in UNCERTAIN_AIRPORTS_TO_DELETE:
                action = 'DELETE'
                status = '[X]'
                # Ajouter une raison spéciale
                reasons_with_manual = reasons + ['Manual review: marked for deletion (military/closed/non-commercial)']
                results['delete'].append({
                    'iata': iata,
                    'label': label,
                    'country': country,
                    'is_commercial': False,
                    'scores': scores,
                    'reasons': reasons_with_manual
                })
            else:
                action = 'REVIEW'
                status = '[?]'
                results['review'].append({
                    'iata': iata,
                    'label': label,
                    'country': country,
                    'is_commercial': None,
                    'scores': scores,
                    'reasons': reasons
                })

        # Affichage en temps réel
        safe_print(f"[{idx}/{len(airports)}] {iata} - {label[:40]}... ({country})")
        safe_print(f"  {status} {action} - Score (C:{scores['commercial']}, NC:{scores['non_commercial']})")
        safe_print(f"  Reasons: {' | '.join(reasons[:2])}...")  # Afficher seulement les 2 premières raisons
        safe_print("")

    return results


def generate_csv_report(results: Dict, output_file: str):
    """Génère le rapport CSV détaillé."""
    logger.info(f"\nGenerating CSV report: {output_file}")

    rows = []

    for category, airports_list in results.items():
        action = category.upper()
        for airport in airports_list:
            rows.append({
                'iata_code': airport['iata'],
                'name': airport['label'],
                'country_code': airport['country'],
                'action': action,
                'is_commercial': airport['is_commercial'],
                'score_commercial': airport['scores']['commercial'],
                'score_non_commercial': airport['scores']['non_commercial'],
                'validation_reasons': ' | '.join(airport['reasons']),
                'in_ourairports': 'Yes' if 'OurAirports:' in ' '.join(airport['reasons']) and 'not found' not in ' '.join(airport['reasons']) else 'No',
                'in_openflights': 'Yes' if 'OpenFlights: present' in ' '.join(airport['reasons']) else 'No'
            })

    df = pd.DataFrame(rows)
    df.to_csv(output_file, index=False)

    logger.info(f"CSV report saved: {output_file}")
    return output_file


def print_statistics(results: Dict):
    """Affiche les statistiques finales."""
    total = len(results['keep']) + len(results['delete']) + len(results['review'])

    safe_print("\n" + "=" * 60)
    safe_print("FINAL STATISTICS")
    safe_print("=" * 60)
    safe_print("")
    safe_print(f"Total Airports Analyzed:    {total}")
    safe_print(f"[OK] Keep (Commercial):       {len(results['keep'])} ({len(results['keep'])/total*100:.1f}%)")
    safe_print(f"[X] Delete (Non-Commercial): {len(results['delete'])} ({len(results['delete'])/total*100:.1f}%)")
    safe_print(f"[?] Uncertain (Review):      {len(results['review'])} ({len(results['review'])/total*100:.1f}%)")
    safe_print("")


def delete_airports(conn, airports_to_delete: List[Dict], dry_run=True) -> int:
    """
    Supprime les aéroports non-commerciaux de la base de données.

    Returns:
        Nombre d'aéroports supprimés
    """
    if dry_run:
        logger.info(f"\n[DRY RUN] Would delete {len(airports_to_delete)} airports")
        for airport in airports_to_delete[:10]:  # Afficher les 10 premiers
            logger.info(f"  - {airport['iata']}: {airport['label']}")
        if len(airports_to_delete) > 10:
            logger.info(f"  ... and {len(airports_to_delete) - 10} more")
        return 0

    # Mode suppression réelle
    logger.info(f"\n[WARNING] About to delete {len(airports_to_delete)} airports")
    confirmation = input("Are you sure you want to proceed? Type 'yes' to confirm: ")

    if confirmation.lower() != 'yes':
        logger.info("[CANCELLED] Deletion cancelled by user")
        return 0

    cursor = conn.cursor()
    deleted_count = 0

    try:
        for airport in airports_to_delete:
            cursor.execute(
                "DELETE FROM airports WHERE iata = %s",
                (airport['iata'],)
            )
            deleted_count += 1
            logger.info(f"Deleted: {airport['iata']} - {airport['label']}")

        conn.commit()
        logger.info(f"\nSuccessfully deleted {deleted_count} airports")

    except Exception as e:
        conn.rollback()
        logger.error(f"[ERROR] Error during deletion: {e}")
        raise
    finally:
        cursor.close()

    return deleted_count


def main():
    """Point d'entrée principal du script."""
    parser = argparse.ArgumentParser(
        description='Clean non-commercial airports from PostgreSQL database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dry-run mode (default, safe)
    python clean_non_commercial_airports.py --dry-run

    # Real deletion mode (⚠️ DANGER)
    python clean_non_commercial_airports.py --delete

    # Force re-download of external sources
    python clean_non_commercial_airports.py --download-sources
        """
    )

    parser.add_argument(
        '--delete',
        action='store_true',
        help='Actually delete non-commercial airports (default is dry-run)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Dry-run mode: show what would be deleted without actually deleting (default)'
    )
    parser.add_argument(
        '--output-report',
        type=str,
        default=None,
        help='Output CSV report filename (default: auto-generated with timestamp)'
    )
    parser.add_argument(
        '--download-sources',
        action='store_true',
        help='Force re-download of external data sources (OurAirports, OpenFlights)'
    )

    args = parser.parse_args()

    # Override dry-run si --delete est spécifié
    if args.delete:
        args.dry_run = False

    # Générer le nom du fichier de rapport
    if args.output_report is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output_report = f'airport_cleanup_report_{timestamp}.csv'

    # Afficher le mode
    mode = "DRY RUN" if args.dry_run else "DELETE"
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Airport Cleanup Script - Mode: {mode}")
    logger.info(f"{'=' * 60}\n")

    # Vérifier la configuration PostgreSQL
    if not all([PG_HOST, PG_USER, PG_PASSWORD]):
        logger.error("[ERROR] PostgreSQL configuration missing. Please check your .env file.")
        logger.error("Required: PG_HOST, PG_USER, PG_PASSWORD")
        sys.exit(1)

    try:
        # 1. Charger les sources de données
        validator = AirportValidator()
        validator.load_sources(force_download=args.download_sources)

        # 2. Connexion à PostgreSQL
        conn = connect_postgres()

        # 3. Récupérer les aéroports
        airports = fetch_airports_from_db(conn)

        # 4. Traiter les aéroports
        results = process_airports(validator, airports)

        # 5. Afficher les statistiques
        print_statistics(results)

        # 6. Générer le rapport CSV
        csv_file = generate_csv_report(results, args.output_report)

        # 7. Supprimer les aéroports (si mode delete)
        deleted_count = delete_airports(conn, results['delete'], dry_run=args.dry_run)

        # 8. Afficher les prochaines étapes
        safe_print("\n" + "=" * 60)
        safe_print("NEXT STEPS")
        safe_print("=" * 60)
        safe_print("")
        safe_print(f"1. Review CSV report: {csv_file}")

        if results['review']:
            safe_print(f"2. Check uncertain airports ({len(results['review'])} need manual review)")

        if args.dry_run:
            safe_print(f"3. Run with --delete flag to execute deletions")
            safe_print(f"   Command: python clean_non_commercial_airports.py --delete")
        else:
            safe_print(f"3. Clear API cache: curl -X POST http://localhost:8000/admin/cache/clear")

        safe_print("")

        if args.dry_run:
            safe_print("[WARNING] This was a DRY RUN. No airports were deleted.")
        else:
            safe_print(f"[SUCCESS] {deleted_count} airports were deleted from the database.")

        safe_print("")

        # Fermer la connexion
        conn.close()

    except Exception as e:
        logger.error(f"[ERROR] Script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
