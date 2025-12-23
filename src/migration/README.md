# Scripts de Migration MongoDB → PostgreSQL/Supabase

Scripts pour migrer les données de pays et de villes depuis MongoDB vers PostgreSQL/Supabase.

## 🚀 Utilisation

### Depuis le répertoire racine

```bash
# Tester les connexions
.venv/Scripts/python.exe -m src.migration.test_connection

# Migrer uniquement les pays
.venv/Scripts/python.exe -m src.migration.migrate_to_postgres

# Migrer uniquement les villes
.venv/Scripts/python.exe -m src.migration.migrate_cities_to_postgres

# Migrer tout (pays + villes)
.venv/Scripts/python.exe -m src.migration.migrate_all
```

### Depuis le répertoire src/migration

```bash
cd src/migration

# Tester les connexions
../../.venv/Scripts/python.exe test_connection.py

# Migrer uniquement les pays
../../.venv/Scripts/python.exe migrate_to_postgres.py

# Migrer uniquement les villes
../../.venv/Scripts/python.exe migrate_cities_to_postgres.py

# Migrer tout (pays + villes)
../../.venv/Scripts/python.exe migrate_all.py

# Enrichir les populations des villes
../../.venv/Scripts/python.exe populate_city_population.py
```

### Wrapper depuis la racine (recommandé)

```bash
# Test de l'environnement
python test_population_setup.py

# Migration MongoDB → PostgreSQL
python migrate.py all

# Enrichissement des populations
python populate_population.py
```

## 📁 Structure

```
src/migration/
├── __init__.py                         # Module Python
├── README.md                           # Ce fichier
├── test_connection.py                  # Test des connexions
├── migrate_to_postgres.py              # Migration des pays
├── migrate_cities_to_postgres.py       # Migration des villes (avec déduplication)
├── migrate_all.py                      # Migration complète
└── populate_city_population.py ⭐      # Enrichissement population (GeoNames + Wikidata)

Racine du projet:
├── migrate.py                          # Wrapper pour migrations
├── populate_population.py              # Wrapper pour enrichissement population
├── test_population_setup.py            # Test environnement
└── POPULATION_ENRICHMENT.md            # Documentation détaillée
```

## ✨ Fonctionnalités

### populate_city_population.py ⭐ NEW
- ✅ **Enrichissement automatique** de la colonne population
- ✅ **GeoNames** comme source primaire (cities15000 dataset)
- ✅ **Wikidata SPARQL** comme fallback pour villes non trouvées
- ✅ **Matching intelligent**: exact + fuzzy (>94% similarité)
- ✅ **Validation géographique**: distance max 30km
- ✅ **Index spatial** pour performance optimale
- ✅ **Progress tracking** avec tqdm
- ✅ **Statistiques détaillées** et résumé final
- ✅ **Batch updates** optimisés (2000 rows par batch)
- ✅ **Gestion d'erreurs robuste** avec retry logic

**Documentation complète**: [POPULATION_ENRICHMENT.md](../../POPULATION_ENRICHMENT.md)

### migrate_cities_to_postgres.py
- ✅ **Déduplication automatique** des villes avec même (slug, country_code)
- ✅ Génération automatique des slugs
- ✅ Création du champ location (PostGIS) depuis latitude/longitude
- ✅ UPSERT pour éviter les duplicatas
- ✅ Logs détaillés avec statistiques de déduplication

### migrate_to_postgres.py
- ✅ Migration des pays avec génération de slugs
- ✅ UPSERT basé sur iso2
- ✅ Gestion robuste des erreurs

## 🐛 Correction du bug de duplicata

Le script `migrate_cities_to_postgres.py` inclut maintenant une **déduplication automatique** avant l'insertion:

```python
cities_dict = {}  # Dictionnaire avec clé (slug, country_code)

for city in cities:
    key = (slug, country_code)

    # Si duplicata, garder celui avec le plus de données
    if key in cities_dict:
        # Logique de sélection intelligente
        ...

    cities_dict[key] = city_data

cities_data = list(cities_dict.values())  # Données uniques
```

Cela résout l'erreur:
```
ON CONFLICT DO UPDATE command cannot affect row a second time
```

## 📊 Logs exemple

```
📊 50000 villes trouvées dans MongoDB
📝 45000 villes uniques prêtes pour l'insertion
   5000 doublons détectés et dédupliqués
   0 villes ignorées
✓ 45000 villes insérées/mises à jour dans PostgreSQL
```

## 📈 Workflow Complet Recommandé

```bash
# 1. Vérifier l'environnement
python test_population_setup.py

# 2. Migrer depuis MongoDB
python migrate.py all

# 3. Enrichir les populations
python populate_population.py

# 4. Vérifier les résultats
# Dans PostgreSQL:
# SELECT COUNT(*),
#        COUNT(population) as with_pop,
#        COUNT(*) - COUNT(population) as without_pop
# FROM cities;
```

## 📚 Documentation complète

- **Migrations**: [README_MIGRATION.md](../../README_MIGRATION.md)
- **Population Enrichment**: [POPULATION_ENRICHMENT.md](../../POPULATION_ENRICHMENT.md)
