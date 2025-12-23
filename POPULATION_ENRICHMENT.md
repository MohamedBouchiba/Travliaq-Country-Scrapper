# Population Enrichment Script

Script pour enrichir la colonne `population` de la table `cities` en utilisant GeoNames et Wikidata.

## Fonctionnement

Le script fonctionne en deux phases:

1. **Phase GeoNames** (source primaire):
   - Télécharge le dataset GeoNames (cities15000.zip par défaut)
   - Construit un index spatial pour des lookups rapides
   - Match les villes par nom exact et fuzzy matching (>94% similarité)
   - Valide la proximité géographique (max 30 km par défaut)

2. **Phase Wikidata** (fallback):
   - Pour les villes non matchées par GeoNames
   - Utilise SPARQL queries géographiques
   - Respect du rate limit (2 QPS par défaut)
   - Match par similarité de nom (>92%)

## Installation

```bash
# Installer les dépendances
pip install tqdm  # Pour les progress bars (optionnel mais recommandé)

# Les autres dépendances sont déjà dans requirements.txt:
# - psycopg2-binary
# - python-dotenv
# - requests
# - httpx
# - rapidfuzz
# - tenacity
# - unidecode
```

## Configuration

Créer ou modifier le fichier `.env`:

```bash
# Database Configuration (Required - Option 1: URL complète)
SUPABASE_DB_URL=postgresql://user:password@host:port/database

# Database Configuration (Required - Option 2: Variables individuelles)
# Utiliser cette option si vous avez déjà les variables PG_* définies
PG_HOST=aws-1-eu-west-3.pooler.supabase.com
PG_DATABASE=postgres
PG_USER=postgres.cinbnmlfpffmyjmkwbco
PG_PASSWORD=cHpcyMx7vrLfKoDF
PG_PORT=5432
PG_SSLMODE=require

# Optional (valeurs par défaut montrées)
GEONAMES_DATASET=cities15000        # ou cities5000, cities1000
MAX_RADIUS_KM=30                    # Distance max pour le matching
WIKIDATA_MAX_QPS=2                  # Requêtes par seconde Wikidata
BATCH_SIZE=2000                     # Taille des batches DB
ONLY_NULL=1                         # 1=seulement NULL, 0=toutes les villes
```

**Note:** Vous pouvez utiliser soit `SUPABASE_DB_URL` (URL complète) soit les variables `PG_*` individuelles. Le script construira automatiquement l'URL si les variables individuelles sont fournies.

### Datasets GeoNames disponibles

- `cities15000`: Villes avec population > 15,000 (~26k records) **[Recommandé]**
- `cities5000`: Villes avec population > 5,000 (~53k records)
- `cities1000`: Villes avec population > 1,000 (~143k records)

## Utilisation

```bash
cd Travliaq-Country-Scrapper

# Exécution basique
python src/migration/populate_city_population.py

# Avec plus de logs
python src/migration/populate_city_population.py 2>&1 | tee population_enrichment.log
```

## Output Exemple

```
============================================================
CITY POPULATION ENRICHMENT SCRIPT
============================================================
GeoNames dataset: cities15000
Max radius: 30 km
Batch size: 2000
Only NULL populations: True
============================================================
Connecting to database...
Database connection established
Fetched 1,234 cities from database
Downloading GeoNames dataset: cities15000
Downloaded 3.2 MB
Parsed 25,793 records from 250 countries
Building spatial index...
Matching against GeoNames...
GeoNames matching: 100%|████████| 1234/1234 [00:02<00:00, 456.78it/s]
Updated 1,050 rows (batch 1)
Matching 184 unmatched cities against Wikidata...
Wikidata queries: 100%|████████| 184/184 [01:32<00:00, 2.00it/s]
Updated 127 rows (batch 1)
============================================================
POPULATION ENRICHMENT SUMMARY
============================================================
Total cities processed:     1,234
GeoNames matches:           1,050 (85.1%)
Wikidata matches:           127 (10.3%)
No match found:             57 (4.6%)
Errors:                     0
Success rate:               95.4%
============================================================
Database connection closed
Script completed successfully
```

## Stratégie de Matching

### GeoNames (Phase 1)

1. **Exact Match**:
   - Nom normalisé correspond exactement
   - Distance < MAX_RADIUS_KM
   - Garde le match le plus proche

2. **Fuzzy Match**:
   - Similarité > 94% (RapidFuzz)
   - Distance < MAX_RADIUS_KM
   - Garde le meilleur score ou le plus proche

### Wikidata (Phase 2)

1. **Geographic Query**:
   - Recherche dans un rayon de 30-50km
   - Filtré par pays (ISO2 code)
   - Uniquement les entités avec population

2. **Match Validation**:
   - Similarité > 92%
   - Distance < MAX_RADIUS_KM
   - Garde le meilleur match

## Normalisation des Noms

Les noms de villes sont normalisés pour le matching:

```python
"Paris" → "paris"
"São Paulo" → "sao paulo"
"New York" → "new york"
"Zürich" → "zurich"
"Île-de-France" → "ile de france"
```

- Lowercase
- Suppression des accents (unidecode)
- Seulement alphanumériques et espaces
- Espaces normalisés

## Performance

### Optimisations

1. **Index Spatial**: Lookup O(1) au lieu de O(n) pour GeoNames
2. **Batch Updates**: Commits par batch de 2000 pour réduire le I/O
3. **Rate Limiting**: Respect des limites Wikidata (2 QPS)
4. **Progress Tracking**: Utilise tqdm pour visibilité
5. **Retry Logic**: Tenacity pour gérer les erreurs réseau

### Temps d'Exécution Estimé

- 1,000 villes: ~3-5 minutes
- 5,000 villes: ~10-20 minutes
- 10,000 villes: ~30-60 minutes

Le temps dépend principalement du nombre de villes non matchées par GeoNames (fallback Wikidata plus lent).

## Gestion d'Erreurs

- **Connexion DB échoue**: Exit avec erreur
- **Download GeoNames échoue**: Exit avec erreur
- **Ligne malformée GeoNames**: Skip silencieux
- **Query Wikidata échoue**: Retry 3x avec backoff exponentiel
- **Ville individuelle échoue**: Log warning, continue

## Mode Debug

Pour activer plus de logs:

```python
# Modifier dans le script
logging.basicConfig(
    level=logging.DEBUG,  # Au lieu de INFO
    ...
)
```

## Maintenance

### Re-exécution

Le script peut être ré-exécuté sans problème:

- Avec `ONLY_NULL=1`: Met à jour seulement les villes sans population
- Avec `ONLY_NULL=0`: Re-process toutes les villes (utile pour refresh)

### Mise à Jour GeoNames

GeoNames est mis à jour quotidiennement. Pour avoir les dernières données:

```bash
# Le script télécharge automatiquement la dernière version
# Pas de cache local
```

## Troubleshooting

### Erreur: "Missing required environment variable: SUPABASE_DB_URL"

Solution: Ajouter `SUPABASE_DB_URL` dans `.env`

### Erreur: "Failed to download GeoNames dataset"

Solutions:
- Vérifier la connexion Internet
- Vérifier que le dataset existe (cities15000, cities5000, cities1000)
- Essayer plus tard (serveur GeoNames peut être down)

### Wikidata rate limit errors

Solution: Réduire `WIKIDATA_MAX_QPS` à 1 ou 0.5

### Trop de "No match found"

Solutions:
- Augmenter `MAX_RADIUS_KM` (ex: 50)
- Utiliser un dataset GeoNames plus large (cities5000 ou cities1000)
- Vérifier la qualité des noms de villes dans la DB

## Architecture du Code

```
populate_city_population.py
├── Configuration & Constants
├── Utilities (normalize_name, haversine_distance)
├── Data Classes
│   ├── CityRecord
│   ├── GeoNamesRecord
│   ├── MatchResult
│   └── Statistics
├── Providers
│   ├── GeoNamesProvider
│   │   ├── download_and_parse()
│   │   ├── _build_spatial_index()
│   │   └── match_city()
│   └── WikidataProvider
│       ├── match_cities() (async)
│       └── _query() (with retry)
└── DatabaseManager
    ├── fetch_cities()
    └── update_populations()
```

## Contribuer

Pour améliorer le script:

1. **Ajouter d'autres sources**: OpenStreetMap Nominatim, etc.
2. **Améliorer le matching**: ML-based name matching
3. **Cache local**: Éviter re-download GeoNames
4. **Parallélisation**: Multiprocessing pour GeoNames matching

## License

Ce script fait partie du projet Travliaq.
