# 🚀 Quick Start - Photos de Pays en 5 Minutes

Guide ultra-rapide pour enrichir vos pays avec des photos.

## ⚡ En bref

1. Obtenir une clé API Unsplash (gratuit)
2. La configurer dans `.env`
3. Lancer le script d'enrichissement
4. Profiter des photos ! 🎉

## 📝 Étapes détaillées

### 1. Obtenir la clé API (2 minutes)

```
1. Allez sur: https://unsplash.com/developers
2. Créez un compte ou connectez-vous
3. Cliquez sur "Your apps" → "New Application"
4. Remplissez le formulaire:
   - Application name: Travliaq Country Photos
   - Description: Photos pour les profils de pays
   ✓ Acceptez les conditions
5. Copiez votre "Access Key"
```

### 2. Configuration (1 minute)

```bash
# Allez dans le dossier du scraper
cd Travliaq-Country-Scrapper

# Créez le fichier .env (si pas déjà fait)
cp .env.example .env

# Éditez .env et ajoutez votre clé
nano .env  # ou code .env, ou vim .env
```

Ajoutez cette ligne :
```env
UNSPLASH_API_KEY=votre_cle_access_ici
```

### 3. Test rapide (30 secondes)

```bash
# Vérifier que tout fonctionne
python test_unsplash_quick.py
```

Résultat attendu :
```
✅ Clé API détectée: AbC123XyZ9...
🔍 Recherche photo pour: France
   ✅ SUCCÈS!
   📸 URL: https://images.unsplash.com/photo-...
...
🎉 L'intégration Unsplash fonctionne correctement!
```

### 4. Enrichissement (15-20 minutes)

```bash
# Option A : Test avec 5 pays d'abord
python enrich_countries_photos.py --dry-run --limit 5

# Option B : Enrichir tous les pays directement
python enrich_countries_photos.py
```

Pendant l'exécution :
```
[1/200] Processing: France (FR)
  ✓ Found photo for France
    URL: https://images.unsplash.com/photo-...
    Credit: Photo by Alex Azabache on Unsplash

[2/200] Processing: Japan (JP)
  ✓ Found photo for Japan
...
```

### 5. Vérification (30 secondes)

```bash
# Vérifier les résultats
python verify_photos_in_db.py
```

Résultat :
```
📊 STATISTIQUES GLOBALES
Total de pays:           200
Avec photo:              175 (87.5%)
Sans photo:              25

✅ 175/200 pays ont une photo (87.5%)
```

## ✅ C'est fait !

Vos pays ont maintenant des photos dans MongoDB.

## 🎯 Prochaine étape : Frontend

Consultez [FRONTEND_INTEGRATION_EXAMPLE.md](FRONTEND_INTEGRATION_EXAMPLE.md) pour afficher les photos sur votre site.

Exemple minimal React :

```tsx
function CountryCard({ country }) {
  return (
    <div className="card">
      <img src={country.photo_url} alt={country.name} />
      <h3>{country.name}</h3>
      <p>{country.photo_credit}</p>
    </div>
  );
}
```

## 🆘 Problèmes ?

### Erreur : "UNSPLASH_API_KEY not found"

➜ Vérifiez que vous avez bien ajouté la clé dans `.env`

```bash
# Vérifier le contenu du .env
cat .env | grep UNSPLASH
```

### Test rapide échoue

```bash
# Vérifier la connexion à Unsplash
curl -I https://api.unsplash.com

# Tester avec une autre clé API
```

### Rate limit dépassé

➜ Attendez 1 heure (limite gratuite : 50 requêtes/heure)

## 📚 Documentation complète

Pour plus de détails :
- [GUIDE_PHOTOS_PAYS.md](GUIDE_PHOTOS_PAYS.md) - Guide détaillé
- [RECAP_PHOTOS_PAYS.md](../RECAP_PHOTOS_PAYS.md) - Vue d'ensemble complète
- [FRONTEND_INTEGRATION_EXAMPLE.md](FRONTEND_INTEGRATION_EXAMPLE.md) - Exemples frontend

## 💡 Commandes utiles

```bash
# Test rapide
python test_unsplash_quick.py

# Dry run avec 5 pays
python enrich_countries_photos.py --dry-run --limit 5

# Enrichir tous les pays
python enrich_countries_photos.py

# Vérifier les résultats
python verify_photos_in_db.py

# Exporter la liste des pays sans photo
python verify_photos_in_db.py --export-missing

# Forcer la mise à jour (même les pays qui ont déjà une photo)
python enrich_countries_photos.py --force-update
```

---

**Temps total : ~20 minutes**

**Questions ? Consultez la doc complète ou contactez l'équipe ! 🚀**
