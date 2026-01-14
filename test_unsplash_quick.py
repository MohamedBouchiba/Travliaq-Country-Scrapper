"""
Quick test script to verify Unsplash integration works.

This script tests the Unsplash API integration without touching the database.
Perfect for verifying your API key and seeing sample results.

Usage:
    python test_unsplash_quick.py
"""

import logging
from src.scrapers.unsplash_photos import UnsplashPhotoScraper, get_country_photo_with_fallbacks
from src.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_unsplash_api():
    """Test Unsplash API with a few sample countries."""

    print("\n" + "=" * 70)
    print("🧪 TEST RAPIDE DE L'API UNSPLASH")
    print("=" * 70 + "\n")

    # Check for API key
    if not hasattr(settings, 'UNSPLASH_API_KEY') or not settings.UNSPLASH_API_KEY:
        print("❌ ERREUR: UNSPLASH_API_KEY non trouvée!")
        print("   Ajoutez votre clé dans le fichier .env")
        print("   Obtenez une clé gratuite: https://unsplash.com/developers\n")
        return False

    print(f"✅ Clé API détectée: {settings.UNSPLASH_API_KEY[:10]}...\n")

    # Initialize scraper
    scraper = UnsplashPhotoScraper()

    # Test countries
    test_countries = [
        "France",
        "Japan",
        "Morocco",
        "Brazil",
        "Iceland"
    ]

    print(f"Test avec {len(test_countries)} pays...\n")
    print("-" * 70 + "\n")

    results = {
        "success": 0,
        "failed": 0
    }

    for country in test_countries:
        print(f"🔍 Recherche photo pour: {country}")

        try:
            photo_data = get_country_photo_with_fallbacks(scraper, country)

            if photo_data:
                print(f"   ✅ SUCCÈS!")
                print(f"   📸 URL: {photo_data['photo_url'][:70]}...")
                print(f"   👤 Crédit: {photo_data['photo_credit']}")
                print(f"   🔗 Source: {photo_data['photo_source']}")
                results["success"] += 1
            else:
                print(f"   ❌ Aucune photo trouvée")
                results["failed"] += 1

        except Exception as e:
            print(f"   ❌ ERREUR: {e}")
            results["failed"] += 1

        print()  # Empty line between countries

    # Summary
    print("-" * 70)
    print("\n📊 RÉSUMÉ")
    print("=" * 70)
    print(f"✅ Photos trouvées:    {results['success']}/{len(test_countries)}")
    print(f"❌ Photos non trouvées: {results['failed']}/{len(test_countries)}")
    print()

    if results["success"] > 0:
        print("🎉 L'intégration Unsplash fonctionne correctement!")
        print("   Vous pouvez maintenant lancer:")
        print("   → python enrich_countries_photos.py --dry-run --limit 5")
        print()
        return True
    else:
        print("⚠️  Aucune photo n'a été trouvée. Vérifiez:")
        print("   1. Votre clé API est valide")
        print("   2. Vous avez une connexion internet")
        print("   3. Vous n'avez pas dépassé la limite de 50 req/heure")
        print()
        return False


if __name__ == "__main__":
    try:
        success = test_unsplash_api()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu par l'utilisateur")
        exit(130)
    except Exception as e:
        print(f"\n\n❌ ERREUR FATALE: {e}")
        exit(1)
