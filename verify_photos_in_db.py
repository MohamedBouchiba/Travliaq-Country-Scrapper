"""
Script de vérification des photos dans MongoDB

Ce script vérifie l'état de l'enrichissement des photos dans la base de données.
Affiche des statistiques détaillées et identifie les pays sans photo.

Usage:
    python verify_photos_in_db.py [--export-missing]

Options:
    --export-missing: Exporte la liste des pays sans photo dans un fichier JSON
"""

import sys
import json
import logging
import argparse
from typing import Dict, List
from src.database import Database
from src.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PhotosVerifier:
    """Vérifie l'état des photos de pays dans MongoDB."""

    def __init__(self, db: Database):
        self.db = db
        self.collection = db.db.countries

    def verify(self) -> Dict:
        """
        Vérifie l'état des photos dans la base de données.

        Returns:
            Dictionnaire avec les statistiques
        """
        print("\n" + "=" * 70)
        print("🔍 VÉRIFICATION DES PHOTOS DE PAYS")
        print("=" * 70 + "\n")

        # Statistiques globales
        total = self.collection.count_documents({})
        with_photo = self.collection.count_documents({
            "photo_url": {"$exists": True, "$ne": None}
        })
        without_photo = total - with_photo

        percentage = (with_photo / total * 100) if total > 0 else 0

        print("📊 STATISTIQUES GLOBALES")
        print("-" * 70)
        print(f"Total de pays:           {total}")
        print(f"Avec photo:              {with_photo} ({percentage:.1f}%)")
        print(f"Sans photo:              {without_photo}")
        print()

        # Vérifier la qualité des données photo
        print("🔍 QUALITÉ DES DONNÉES")
        print("-" * 70)

        # Pays avec photo mais sans crédit
        no_credit = self.collection.count_documents({
            "photo_url": {"$exists": True, "$ne": None},
            "photo_credit": {"$exists": False}
        })
        print(f"Photos sans crédit:      {no_credit}")

        # Pays avec photo mais sans source
        no_source = self.collection.count_documents({
            "photo_url": {"$exists": True, "$ne": None},
            "photo_source": {"$exists": False}
        })
        print(f"Photos sans source:      {no_source}")
        print()

        # Statistiques par région
        print("🌍 STATISTIQUES PAR RÉGION")
        print("-" * 70)

        pipeline = [
            {
                "$group": {
                    "_id": "$region",
                    "total": {"$sum": 1},
                    "with_photo": {
                        "$sum": {
                            "$cond": [
                                {"$and": [
                                    {"$ifNull": ["$photo_url", False]},
                                    {"$ne": ["$photo_url", None]}
                                ]},
                                1,
                                0
                            ]
                        }
                    }
                }
            },
            {"$sort": {"total": -1}}
        ]

        regions = list(self.collection.aggregate(pipeline))

        for region in regions:
            region_name = region["_id"] or "Non défini"
            total_region = region["total"]
            with_photo_region = region["with_photo"]
            pct = (with_photo_region / total_region * 100) if total_region > 0 else 0

            print(f"{region_name:20} {with_photo_region:3}/{total_region:3} ({pct:5.1f}%)")

        # Liste des pays sans photo
        print("\n" + "=" * 70)
        print("❌ PAYS SANS PHOTO")
        print("=" * 70 + "\n")

        countries_without_photo = list(self.collection.find(
            {
                "$or": [
                    {"photo_url": {"$exists": False}},
                    {"photo_url": None}
                ]
            },
            {
                "name": 1,
                "code_iso2": 1,
                "region": 1,
                "_id": 0
            }
        ).sort("name", 1))

        if countries_without_photo:
            print(f"Total: {len(countries_without_photo)} pays\n")

            # Grouper par région
            by_region: Dict[str, List[Dict]] = {}
            for country in countries_without_photo:
                region = country.get("region", "Non défini")
                if region not in by_region:
                    by_region[region] = []
                by_region[region].append(country)

            for region, countries in sorted(by_region.items()):
                print(f"\n{region} ({len(countries)} pays):")
                print("-" * 70)
                for country in countries:
                    print(f"  • {country['name']} ({country['code_iso2']})")
        else:
            print("✅ Tous les pays ont une photo !")

        # Exemples de pays avec photo
        print("\n" + "=" * 70)
        print("✅ EXEMPLES DE PAYS AVEC PHOTO")
        print("=" * 70 + "\n")

        examples = list(self.collection.find(
            {"photo_url": {"$exists": True, "$ne": None}},
            {
                "name": 1,
                "code_iso2": 1,
                "photo_url": 1,
                "photo_credit": 1,
                "_id": 0
            }
        ).limit(5))

        for country in examples:
            print(f"🌍 {country['name']} ({country['code_iso2']})")
            print(f"   📸 {country.get('photo_url', 'N/A')[:70]}...")
            print(f"   👤 {country.get('photo_credit', 'N/A')}")
            print()

        return {
            "total": total,
            "with_photo": with_photo,
            "without_photo": without_photo,
            "percentage": percentage,
            "no_credit": no_credit,
            "no_source": no_source,
            "countries_without_photo": countries_without_photo
        }

    def export_missing(self, filename: str = "countries_without_photo.json"):
        """
        Exporte la liste des pays sans photo dans un fichier JSON.

        Args:
            filename: Nom du fichier de sortie
        """
        countries_without_photo = list(self.collection.find(
            {
                "$or": [
                    {"photo_url": {"$exists": False}},
                    {"photo_url": None}
                ]
            },
            {
                "name": 1,
                "code_iso2": 1,
                "region": 1,
                "capital": 1,
                "_id": 0
            }
        ).sort("name", 1))

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(countries_without_photo, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Liste exportée dans {filename}")
        print(f"   {len(countries_without_photo)} pays sans photo")


def main():
    """Point d'entrée du script."""
    parser = argparse.ArgumentParser(
        description="Vérifie l'état des photos de pays dans MongoDB"
    )
    parser.add_argument(
        "--export-missing",
        action="store_true",
        help="Exporte la liste des pays sans photo dans un fichier JSON"
    )

    args = parser.parse_args()

    try:
        # Connexion à la base de données
        db = Database()
        db.connect()  # Connect to MongoDB
        verifier = PhotosVerifier(db)

        # Vérification
        stats = verifier.verify()

        # Export si demandé
        if args.export_missing and stats["countries_without_photo"]:
            verifier.export_missing()

        # Résumé final
        print("\n" + "=" * 70)
        print("📋 RÉSUMÉ")
        print("=" * 70)
        print(f"✅ {stats['with_photo']}/{stats['total']} pays ont une photo ({stats['percentage']:.1f}%)")

        if stats["without_photo"] > 0:
            print(f"⚠️  {stats['without_photo']} pays n'ont pas encore de photo")
            print(f"\n💡 Pour enrichir ces pays, utilisez:")
            print(f"   python enrich_countries_photos.py")
        else:
            print(f"\n🎉 Tous les pays ont une photo !")

        if stats["no_credit"] > 0 or stats["no_source"] > 0:
            print(f"\n⚠️  Attention: {stats['no_credit']} photos sans crédit, {stats['no_source']} sans source")

        print()

        sys.exit(0)

    except Exception as e:
        logger.error(f"Erreur lors de la vérification: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
