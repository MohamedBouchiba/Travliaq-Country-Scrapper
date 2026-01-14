# 🚀 Installation - Enrichissement Photos de Pays

## ✅ Fichier .env créé !

Le fichier `.env` a été créé avec vos identifiants :
- ✅ MongoDB URI configurée
- ✅ Clé API Unsplash configurée
- ✅ Tous les paramètres prêts

## 📦 Installation des dépendances

### Option 1 : Avec pip (recommandé)

```bash
cd /home/mohamed-bouchiba/Bureau/Travliaq/Travliaq-Country-Scrapper

# Installer pip si nécessaire
sudo apt update
sudo apt install python3-pip -y

# Installer les dépendances
pip3 install -r requirements.txt
```

### Option 2 : Avec un environnement virtuel (meilleure pratique)

```bash
cd /home/mohamed-bouchiba/Bureau/Travliaq/Travliaq-Country-Scrapper

# Créer un environnement virtuel
python3 -m venv .venv

# Activer l'environnement virtuel
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

## ✨ Test rapide

Une fois les dépendances installées :

```bash
# Test de l'API Unsplash (30 secondes)
python3 test_unsplash_quick.py
```

Résultat attendu :
```
✅ Clé API détectée: tRIhhKnaa2...
🔍 Recherche photo pour: France
   ✅ SUCCÈS!
   📸 URL: https://images.unsplash.com/photo-...
   👤 Crédit: Photo by Alex Azabache on Unsplash
...
🎉 L'intégration Unsplash fonctionne correctement!
```

## 🚀 Enrichissement des pays

```bash
# Test avec 5 pays (mode dry-run, ne modifie pas la BDD)
python3 enrich_countries_photos.py --dry-run --limit 5

# Si le test est OK, enrichir tous les pays
python3 enrich_countries_photos.py
```

## 📊 Vérification des résultats

```bash
# Voir les statistiques
python3 verify_photos_in_db.py
```

## 🎯 Commandes rapides avec Makefile

Si vous avez `make` installé :

```bash
make install      # Installer les dépendances
make test-api     # Test rapide
make enrich       # Enrichir tous les pays
make verify       # Voir les stats
```

## 🆘 Dépannage

### "No module named 'pydantic_settings'"

```bash
pip3 install pydantic pydantic-settings
```

### "No module named 'requests'"

```bash
pip3 install requests
```

### "No module named 'pymongo'"

```bash
pip3 install pymongo motor
```

### Installer toutes les dépendances manuellement

```bash
pip3 install requests pydantic pydantic-settings pymongo motor python-dotenv
```

## 📚 Prochaines étapes

1. **Installer les dépendances** (voir ci-dessus)
2. **Tester l'API** : `python3 test_unsplash_quick.py`
3. **Enrichir les pays** : `python3 enrich_countries_photos.py`
4. **Consulter la doc** : [QUICK_START_PHOTOS.md](QUICK_START_PHOTOS.md)

---

**Bon enrichissement ! 🌍📸**
