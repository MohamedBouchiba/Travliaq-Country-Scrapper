# Makefile pour Travliaq-Country-Scrapper
# Usage: make <target>

.PHONY: help install test-api enrich-dry enrich verify export-missing clean

# Afficher l'aide
help:
	@echo "📸 Travliaq Country Photos - Commandes disponibles"
	@echo ""
	@echo "Configuration:"
	@echo "  make install          Installer les dépendances"
	@echo ""
	@echo "Tests:"
	@echo "  make test-api         Tester l'API Unsplash (5 pays)"
	@echo "  make enrich-dry       Test d'enrichissement (10 pays, dry-run)"
	@echo ""
	@echo "Enrichissement:"
	@echo "  make enrich           Enrichir TOUS les pays avec photos"
	@echo "  make enrich-force     Forcer la mise à jour (même pays avec photo)"
	@echo ""
	@echo "Vérification:"
	@echo "  make verify           Vérifier l'état des photos dans MongoDB"
	@echo "  make export-missing   Exporter les pays sans photo (JSON)"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean            Nettoyer les fichiers temporaires"
	@echo ""

# Installer les dépendances
install:
	@echo "📦 Installation des dépendances..."
	pip install -r requirements.txt
	@echo "✅ Dépendances installées !"

# Test rapide de l'API
test-api:
	@echo "🧪 Test de l'API Unsplash..."
	python test_unsplash_quick.py

# Test d'enrichissement en mode dry-run
enrich-dry:
	@echo "🧪 Test d'enrichissement (10 pays, dry-run)..."
	python enrich_countries_photos.py --dry-run --limit 10

# Enrichir tous les pays
enrich:
	@echo "📸 Enrichissement de TOUS les pays..."
	@echo "⏱️  Cela peut prendre 15-20 minutes..."
	python enrich_countries_photos.py

# Forcer la mise à jour
enrich-force:
	@echo "🔄 Mise à jour forcée (tous les pays)..."
	python enrich_countries_photos.py --force-update

# Vérifier l'état
verify:
	@echo "🔍 Vérification de l'état des photos..."
	python verify_photos_in_db.py

# Exporter les pays sans photo
export-missing:
	@echo "📤 Export des pays sans photo..."
	python verify_photos_in_db.py --export-missing

# Nettoyer
clean:
	@echo "🧹 Nettoyage..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".DS_Store" -delete
	rm -f countries_without_photo.json
	@echo "✅ Nettoyage terminé !"
