# Migration MongoDB → PostgreSQL/Supabase

Scripts simples pour migrer les données de MongoDB vers PostgreSQL/Supabase.

## 🚀 Démarrage rapide

```bash
# 1. Installer les dépendances
pip install psycopg2-binary

# 2. Configurer le .env avec vos credentials PostgreSQL
# (PG_HOST, PG_USER, PG_PASSWORD, etc.)

# 3. Tester la connexion
.venv/Scripts/python.exe migrate.py test

# 4. Migrer tout
.venv/Scripts/python.exe migrate.py all
```

## 📁 Structure des fichiers

```
Travliaq-Country-Scrapper/
├── src/
│   └── migration/              # 📂 Module de migration
│       ├── __init__.py
│       ├── README.md
│       ├── test_connection.py
│       ├── migrate_to_postgres.py         # Migration pays
│       ├── migrate_cities_to_postgres.py  # Migration villes (avec déduplication)
│       └── migrate_all.py                 # Migration complète
├── migrate.py                  # 🚀 Script raccourci (recommandé)
├── create_tables.sql           # Script SQL pour créer les tables
├── requirements-migration.txt  # Dépendances Python
└── README_MIGRATION.md         # Ce fichier
```

## 🎯 Utilisation du script raccourci (RECOMMANDÉ)

Le script `migrate.py` à la racine permet de lancer facilement les migrations:

```bash
# Tester les connexions
.venv/Scripts/python.exe migrate.py test

# Migrer uniquement les pays
.venv/Scripts/python.exe migrate.py countries

# Migrer uniquement les villes
.venv/Scripts/python.exe migrate.py cities

# Migrer tout (pays + villes)
.venv/Scripts/python.exe migrate.py all

# Afficher l'aide
.venv/Scripts/python.exe migrate.py --help
```

## 📋 Scripts disponibles

| Script | Description |
|--------|-------------|
| `migrate.py test` | Teste les connexions MongoDB et PostgreSQL |
| `migrate.py countries` | Migre uniquement les **pays** |
| `migrate.py cities` | Migre uniquement les **villes** (avec déduplication) |
| `migrate.py all` | Migre **tout** (pays + villes) - **RECOMMANDÉ** |

## ✨ Fonctionnalités

- ✅ Migration automatique avec UPSERT (pas de duplicatas)
- ✅ **Déduplication automatique des villes** (fix du bug)
- ✅ Génération automatique des slugs
- ✅ Support PostGIS pour les coordonnées géographiques
- ✅ Logs détaillés et rapports de migration
- ✅ Gestion des erreurs robuste
- ✅ Idempotent (peut être relancé sans problème)

## 🐛 Correction du bug de duplicata

Le script `migrate_cities_to_postgres.py` inclut maintenant une **déduplication automatique** qui résout l'erreur:

```
ON CONFLICT DO UPDATE command cannot affect row a second time
```

Avant l'insertion, les villes avec le même `(slug, country_code)` sont dédupliquées intelligemment:
- Garde la ville avec le plus de données (population, coordonnées, etc.)
- Affiche des statistiques de déduplication dans les logs

Exemple de logs:
```
📊 50000 villes trouvées dans MongoDB
📝 45000 villes uniques prêtes pour l'insertion
   5000 doublons détectés et dédupliqués
   0 villes ignorées
✓ 45000 villes insérées/mises à jour dans PostgreSQL
```

## 🎯 Tables migrées

### Countries (Pays)
- Clé primaire: `iso2`
- Champs: iso2, iso3, name, slug, population, region, subregion
- Auto-généré: slug

### Cities (Villes)
- Clé unique: `(slug, country_code)`
- Champs: name, country, country_code, slug, latitude, longitude, location, state_code, state_name, population
- Auto-générés: slug, location (PostGIS)

## 📋 Prérequis

1. **MongoDB** avec les collections `countries` et `cities`
2. **PostgreSQL/Supabase** avec les tables créées (voir `create_tables.sql`)
3. **Python 3.8+** avec les packages: pymongo, psycopg2-binary, python-dotenv

## 🔧 Configuration

Fichier `.env`:
```env
# MongoDB
MONGODB_URI=mongodb+srv://...
DB_NAME=travliaq_knowledge_base

# PostgreSQL/Supabase
PG_HOST=aws-1-eu-west-3.pooler.supabase.com
PG_DATABASE=postgres
PG_USER=postgres.xxxxxxxxx
PG_PASSWORD=votre_mot_de_passe
PG_PORT=5432
PG_SSLMODE=require
```

## 📊 Résultat attendu

```
🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍
🚀 Migration complète MongoDB → PostgreSQL
🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍

🏳️  Étape 1/2: Migration des pays...
✓ 195 pays migrés

🏙️  Étape 2/2: Migration des villes...
📊 50000 villes trouvées dans MongoDB
📝 45000 villes uniques prêtes pour l'insertion
   5000 doublons détectés et dédupliqués
✓ 45000 villes migrées

✅ Migration complète terminée avec succès!
```

## 📚 Documentation détaillée

- [src/migration/README.md](src/migration/README.md) - Documentation du module de migration
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Guide complet (si disponible)
- [create_tables.sql](create_tables.sql) - Script SQL pour créer les tables
