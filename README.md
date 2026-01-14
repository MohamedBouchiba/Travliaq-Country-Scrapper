# Travliaq-Country-Scrapper

Service de base de connaissance voyage pour Travliaq. Ce projet récupère et synchronise quotidiennement des informations sur les pays et les villes dans MongoDB Atlas.

## 🎯 Objectif

Construire une source de vérité fiable pour :

- Les informations pays (codes, devises, langues, etc.)
- Les informations villes (géolocalisation, etc.)

## 🚀 Démarrage Rapide

### Prérequis

- Python 3.10+
- MongoDB Atlas (ou local)

### Installation

1. Cloner le repo
2. Créer un environnement virtuel :

   **Windows (Git Bash) :**

   ```bash
   python -m venv .venv
   source .venv/Scripts/activate
   ```

   **Mac/Linux :**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

Créer un fichier `.env` à la racine :

```ini
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
DB_NAME=travliaq_knowledge_base
LOG_LEVEL=INFO
```

### Lancement

```bash
# Lancer la synchronisation manuellement
python -m src.main
```

## 🐳 Docker

Le projet est conçu pour tourner dans un conteneur (ex: Cron Job sur Railway).

```bash
# Build
docker build -t travliaq-country-scrapper .

# Run
docker run --env-file .env travliaq-country-scrapper
```

## 🏗 Architecture

- `src/main.py` : Point d'entrée.
- `src/database.py` : Gestion de la connexion MongoDB et des opérations Upsert (Idempotence).
- `src/scrapers/` : Modules de récupération de données (ex: `restcountries.py`).
- `src/services/synchronizer.py` : Orchestrateur qui appelle les scrapers et sauvegarde en base.

## 🔄 Mises à jour

Le script est idempotent. Il peut être lancé tous les jours sans créer de doublons (utilise `code_iso2` comme clé unique pour les pays).

## 📸 Enrichissement avec Photos (NOUVEAU!)

Le projet inclut maintenant un système d'enrichissement automatique des pays avec des photos d'illustration de haute qualité depuis Unsplash.

### Configuration rapide

1. Obtenez une clé API Unsplash gratuite: [https://unsplash.com/developers](https://unsplash.com/developers)
2. Ajoutez-la dans votre `.env` :
   ```ini
   UNSPLASH_API_KEY=votre_cle_access_ici
   ```

### Utilisation

```bash
# Test rapide de l'API (sans toucher la base de données)
python test_unsplash_quick.py

# Test avec 5 pays en mode dry-run
python enrich_countries_photos.py --dry-run --limit 5

# Enrichir tous les pays
python enrich_countries_photos.py
```

### Documentation complète

📚 Consultez le guide détaillé: [GUIDE_PHOTOS_PAYS.md](GUIDE_PHOTOS_PAYS.md)

Le guide comprend:
- ✅ Configuration pas à pas
- ✅ Exemples d'utilisation
- ✅ Personnalisation des recherches par pays
- ✅ Intégration frontend
- ✅ Dépannage

### Résultats attendus

Pour chaque pays, les champs suivants sont ajoutés:
- `photo_url`: URL de la photo haute qualité
- `photo_credit`: Attribution du photographe
- `photo_source`: Lien vers le profil du photographe
