# Guide d'enrichissement des photos de pays

## Vue d'ensemble

Ce guide explique comment enrichir votre base de données MongoDB avec des photos d'illustration de haute qualité pour chaque pays, en utilisant l'API Unsplash.

## Pourquoi Unsplash ?

✅ **Avantages :**
- Photos de très haute qualité et professionnelles
- Gratuites à utiliser (avec attribution)
- API officielle fiable et bien documentée
- Large collection de photos de paysages et monuments
- Légal et conforme aux licences

## Configuration

### 1. Obtenir une clé API Unsplash (GRATUIT)

1. Allez sur [https://unsplash.com/developers](https://unsplash.com/developers)
2. Créez un compte Unsplash (si vous n'en avez pas)
3. Cliquez sur "Register as a developer"
4. Créez une nouvelle application ("New Application")
   - **Application name:** Travliaq Country Photos
   - **Description:** Enrichment des profils de pays avec des photos représentatives
   - Acceptez les conditions d'utilisation
5. Copiez votre **Access Key**

### 2. Configurer l'environnement

Ajoutez votre clé API dans le fichier `.env` :

```bash
cd Travliaq-Country-Scrapper
cp .env.example .env  # Si vous n'avez pas encore de fichier .env
```

Éditez `.env` et ajoutez :

```env
UNSPLASH_API_KEY=votre_cle_access_unsplash_ici
```

### 3. Vérifier les dépendances

Le scraper utilise la bibliothèque `requests` qui est déjà dans vos dépendances :

```bash
pip install -r requirements.txt
```

## Utilisation

### Mode test (Dry Run)

Avant de modifier la base de données, testez d'abord avec quelques pays :

```bash
# Test avec 5 pays seulement, sans modifier la base de données
python enrich_countries_photos.py --dry-run --limit 5
```

Vous verrez :
```
[1/5] Processing: France (FR)
  ✓ Found photo for France
    URL: https://images.unsplash.com/photo-1502602898657...
    Credit: Photo by John Doe on Unsplash
  [DRY RUN] Would update database

[2/5] Processing: Japan (JP)
  ✓ Found photo for Japan
...
```

### Enrichir tous les pays

Une fois satisfait du test, lancez l'enrichissement complet :

```bash
python enrich_countries_photos.py
```

Cette commande :
- ✅ Traite tous les pays dans MongoDB
- ✅ Saute les pays qui ont déjà une photo
- ✅ Recherche des photos pertinentes (monuments, paysages)
- ✅ Ajoute l'attribution correcte (crédit photographe)
- ✅ Affiche un résumé à la fin

### Options avancées

```bash
# Traiter seulement les 10 premiers pays
python enrich_countries_photos.py --limit 10

# Forcer la mise à jour même pour les pays ayant déjà une photo
python enrich_countries_photos.py --force-update

# Dry run pour tout voir sans modifier
python enrich_countries_photos.py --dry-run
```

## Structure des données ajoutées

Pour chaque pays, les champs suivants sont ajoutés dans MongoDB :

```javascript
{
  "name": "France",
  "code_iso2": "FR",
  // ... autres champs existants ...

  // Nouveaux champs :
  "photo_url": "https://images.unsplash.com/photo-1502602898657...",
  "photo_credit": "Photo by Alex Azabache on Unsplash",
  "photo_source": "https://unsplash.com/@alexazabache"
}
```

### Utilisation dans votre frontend

```typescript
// Exemple d'utilisation dans React
function CountryCard({ country }) {
  return (
    <div className="country-card">
      <img
        src={country.photo_url}
        alt={country.name}
        loading="lazy"
      />
      <h3>{country.name}</h3>
      <p className="photo-credit">{country.photo_credit}</p>
    </div>
  );
}
```

## Stratégie de recherche intelligente

Le scraper utilise une stratégie de recherche en cascade :

1. **Recherche spécifique** pour les pays majeurs (voir `COUNTRY_SPECIFIC_QUERIES`)
   - Exemple pour France : "Eiffel Tower Paris", "French Riviera"
   - Exemple pour Japon : "Mount Fuji", "Tokyo skyline"

2. **Recherche générique** pour les autres pays :
   - "{pays} landmark"
   - "{pays} landscape"
   - "{pays} architecture"
   - "{pays} travel"

Cela garantit les meilleures photos possibles !

## Personnalisation

### Ajouter vos propres recherches pour certains pays

Éditez [enrich_countries_photos.py](enrich_countries_photos.py) ligne 121+ pour ajouter vos pays :

```python
COUNTRY_SPECIFIC_QUERIES = {
    "Maroc": ["Marrakech medina", "Chefchaouen blue city"],
    "Tunisie": ["Sidi Bou Said", "Sahara desert Tunisia"],
    # Ajoutez vos pays ici
}
```

### Changer la qualité de l'image

Dans [src/scrapers/unsplash_photos.py](src/scrapers/unsplash_photos.py) ligne 89 :

```python
# Options disponibles :
# - "raw": qualité maximale (très lourd)
# - "full": haute résolution
# - "regular": bonne qualité (recommandé) ⭐
# - "small": petite taille
# - "thumb": miniature

photo_url = photo["urls"]["regular"]  # Changez "regular" si nécessaire
```

## Limites de l'API Unsplash

**GRATUIT :**
- ✅ 50 requêtes par heure (mode Demo)
- ✅ Suffisant pour ~200 pays avec la stratégie de cascade

**Production (si besoin) :**
- 5000 requêtes par heure
- Nécessite d'upgrader l'application sur Unsplash (toujours gratuit)

## Vérification des résultats

### Vérifier dans MongoDB

```javascript
// Connexion à MongoDB
use travliaq_knowledge_base

// Compter les pays avec photos
db.countries.countDocuments({ photo_url: { $exists: true, $ne: null } })

// Voir un exemple
db.countries.findOne({ photo_url: { $exists: true } })

// Voir tous les pays SANS photo
db.countries.find(
  { photo_url: { $exists: false } },
  { name: 1, code_iso2: 1 }
)
```

### Consulter les logs

Les logs détaillés sont affichés pendant l'exécution :
- ✓ Photo trouvée
- ✗ Photo non trouvée
- ↳ Pays ignoré (déjà une photo)

## Dépannage

### Erreur : "UNSPLASH_API_KEY not found"

➜ Vérifiez que vous avez bien ajouté la clé dans `.env`

### Erreur : "Rate limit exceeded"

➜ Vous avez dépassé les 50 requêtes/heure. Attendez 1 heure ou upgrader votre app Unsplash.

### Certains pays n'ont pas de photo

➜ Normal ! Certains pays très petits ou peu connus peuvent ne pas avoir de photos pertinentes.
➜ Solution : Ajoutez des recherches manuelles dans `COUNTRY_SPECIFIC_QUERIES`

### Photos non pertinentes

➜ Personnalisez les requêtes dans `COUNTRY_SPECIFIC_QUERIES` pour ce pays spécifique

## Alternative : Photos manuelles

Si vous préférez utiliser vos propres photos ou d'autres sources :

1. **Wikimedia Commons** (gratuit, libre de droits)
2. **Pexels** (alternative à Unsplash)
3. **Upload manuel** dans un bucket S3/Cloudinary

Exemple avec Wikimedia :
```python
# Ajoutez un nouveau scraper similaire à unsplash_photos.py
# API Wikimedia : https://commons.wikimedia.org/wiki/Commons:API
```

## Respect de la licence Unsplash

**IMPORTANT** : Vous DEVEZ afficher l'attribution sur votre site :

```html
<!-- Exemple d'affichage correct -->
<img src="https://images.unsplash.com/..." alt="France">
<p>Photo by Alex Azabache on Unsplash</p>
```

Ou avec un lien :
```html
<a href="https://unsplash.com/@alexazabache">Photo by Alex Azabache</a> on <a href="https://unsplash.com">Unsplash</a>
```

## Statistiques attendues

Pour ~200 pays :
- ⏱️ Temps d'exécution : ~15-20 minutes
- ✅ Photos trouvées : ~85-90% des pays
- ❌ Photos non trouvées : ~10-15% (petits pays, îles peu connues)

## Support

Questions ? Problèmes ?
- Vérifiez les logs détaillés
- Testez d'abord avec `--dry-run --limit 1`
- Consultez la documentation Unsplash API : https://unsplash.com/documentation

---

**Bon enrichissement ! 🌍📸**
