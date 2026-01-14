#!/bin/bash

# Script d'installation et de test du système de photos de pays
# Usage: bash setup.sh

set -e  # Exit on error

echo "======================================================================"
echo "🚀 Installation - Système de Photos de Pays"
echo "======================================================================"
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Étape 1: Vérifier Python
echo "📦 Étape 1/5: Vérification de Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 n'est pas installé${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ $PYTHON_VERSION trouvé${NC}"
echo ""

# Étape 2: Installer python3-venv si nécessaire
echo "📦 Étape 2/5: Vérification de python3-venv..."
if ! dpkg -l | grep -q python3-venv; then
    echo -e "${YELLOW}⚠️  python3-venv n'est pas installé${NC}"
    echo "Pour l'installer, exécutez: sudo apt install python3-venv python3-full -y"
    echo ""
    echo "Continuons sans environnement virtuel (utilisation de --break-system-packages)..."
    USE_VENV=false
else
    echo -e "${GREEN}✅ python3-venv est installé${NC}"
    USE_VENV=true
fi
echo ""

# Étape 3: Créer l'environnement virtuel ou installer globalement
if [ "$USE_VENV" = true ]; then
    echo "📦 Étape 3/5: Création de l'environnement virtuel..."
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        echo -e "${GREEN}✅ Environnement virtuel créé${NC}"
    else
        echo -e "${YELLOW}⚠️  Environnement virtuel déjà existant${NC}"
    fi

    # Activer l'environnement virtuel
    source .venv/bin/activate
    echo -e "${GREEN}✅ Environnement virtuel activé${NC}"
    echo ""

    # Installer les dépendances
    echo "📦 Étape 4/5: Installation des dépendances..."
    pip install -r requirements.txt
else
    echo "📦 Étape 3/5: Pas d'environnement virtuel (sauté)"
    echo ""
    echo "📦 Étape 4/5: Installation des dépendances..."
    python3 -m pip install -r requirements.txt --break-system-packages
fi

echo -e "${GREEN}✅ Dépendances installées${NC}"
echo ""

# Étape 5: Vérifier le fichier .env
echo "📦 Étape 5/5: Vérification de la configuration..."
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Fichier .env non trouvé${NC}"
    echo "Le fichier .env devrait déjà exister avec vos credentials"
    exit 1
fi

# Vérifier la clé Unsplash
if grep -q "UNSPLASH_API_KEY=tRIhhKnaa26iHogTVcd781JdBj0UuCulCkAblqLtbX4" .env; then
    echo -e "${GREEN}✅ Clé API Unsplash configurée${NC}"
else
    echo -e "${YELLOW}⚠️  Clé API Unsplash non trouvée dans .env${NC}"
fi

# Vérifier MongoDB URI
if grep -q "MONGODB_URI=mongodb" .env; then
    echo -e "${GREEN}✅ MongoDB URI configurée${NC}"
else
    echo -e "${RED}❌ MongoDB URI non trouvée dans .env${NC}"
fi
echo ""

# Test rapide de l'API
echo "======================================================================"
echo "🧪 Test de l'API Unsplash"
echo "======================================================================"
echo ""

if [ "$USE_VENV" = true ]; then
    python test_unsplash_quick.py
else
    python3 test_unsplash_quick.py
fi

echo ""
echo "======================================================================"
echo "✅ Installation terminée avec succès !"
echo "======================================================================"
echo ""
echo "Prochaines étapes:"
echo ""
if [ "$USE_VENV" = true ]; then
    echo "1. Activer l'environnement virtuel (si pas déjà fait):"
    echo "   source .venv/bin/activate"
    echo ""
    echo "2. Test avec 5 pays (dry-run):"
    echo "   python enrich_countries_photos.py --dry-run --limit 5"
    echo ""
    echo "3. Enrichir tous les pays:"
    echo "   python enrich_countries_photos.py"
    echo ""
    echo "4. Vérifier les résultats:"
    echo "   python verify_photos_in_db.py"
else
    echo "1. Test avec 5 pays (dry-run):"
    echo "   python3 enrich_countries_photos.py --dry-run --limit 5"
    echo ""
    echo "2. Enrichir tous les pays:"
    echo "   python3 enrich_countries_photos.py"
    echo ""
    echo "3. Vérifier les résultats:"
    echo "   python3 verify_photos_in_db.py"
fi
echo ""
