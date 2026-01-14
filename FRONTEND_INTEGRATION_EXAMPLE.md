# Intégration Frontend - Exemples d'utilisation des photos de pays

Ce document montre comment utiliser les photos de pays enrichies dans votre application frontend (React/TypeScript).

## 1. Mise à jour du type TypeScript

Ajoutez les nouveaux champs photo à votre interface Country :

```typescript
// types/country.ts
export interface Country {
  name: string;
  code_iso2: string;
  code_iso3?: string;
  capital?: string[];
  region?: string;
  subregion?: string;
  population?: number;
  flags?: {
    png?: string;
    svg?: string;
  };

  // Nouveaux champs photo
  photo_url?: string;
  photo_credit?: string;
  photo_source?: string;

  // Autres champs...
  daily_budget_min?: number;
  daily_budget_max?: number;
}
```

## 2. Composant Card de Pays avec Photo

### Exemple simple

```tsx
// components/CountryCard.tsx
import React from 'react';
import { Country } from '@/types/country';

interface CountryCardProps {
  country: Country;
}

export const CountryCard: React.FC<CountryCardProps> = ({ country }) => {
  return (
    <div className="country-card">
      {/* Photo de fond */}
      {country.photo_url && (
        <div className="country-image-container">
          <img
            src={country.photo_url}
            alt={country.name}
            loading="lazy"
            className="country-image"
          />
          {/* Overlay gradient pour la lisibilité */}
          <div className="image-overlay" />
        </div>
      )}

      {/* Contenu */}
      <div className="country-content">
        <h3 className="country-name">{country.name}</h3>

        {country.capital && (
          <p className="country-capital">📍 {country.capital[0]}</p>
        )}

        {/* Crédit photo (important pour Unsplash!) */}
        {country.photo_credit && (
          <p className="photo-credit">
            {country.photo_source ? (
              <a
                href={country.photo_source}
                target="_blank"
                rel="noopener noreferrer"
              >
                {country.photo_credit}
              </a>
            ) : (
              country.photo_credit
            )}
          </p>
        )}
      </div>
    </div>
  );
};
```

### CSS Tailwind

```tsx
// components/CountryCard.tsx (avec Tailwind)
export const CountryCard: React.FC<CountryCardProps> = ({ country }) => {
  return (
    <div className="relative overflow-hidden rounded-lg shadow-lg hover:shadow-xl transition-shadow">
      {/* Photo de fond */}
      {country.photo_url && (
        <div className="relative h-64">
          <img
            src={country.photo_url}
            alt={country.name}
            loading="lazy"
            className="w-full h-full object-cover"
          />
          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
        </div>
      )}

      {/* Contenu */}
      <div className="absolute bottom-0 left-0 right-0 p-4 text-white">
        <h3 className="text-2xl font-bold mb-1">{country.name}</h3>

        {country.capital && (
          <p className="text-sm opacity-90">📍 {country.capital[0]}</p>
        )}

        {/* Crédit photo */}
        {country.photo_credit && (
          <p className="text-xs opacity-70 mt-2">
            {country.photo_source ? (
              <a
                href={country.photo_source}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:underline"
              >
                {country.photo_credit}
              </a>
            ) : (
              country.photo_credit
            )}
          </p>
        )}
      </div>
    </div>
  );
};
```

## 3. Composant Hero avec Photo de Pays

```tsx
// components/CountryHero.tsx
export const CountryHero: React.FC<{ country: Country }> = ({ country }) => {
  return (
    <div className="relative h-screen w-full">
      {/* Background image */}
      {country.photo_url && (
        <>
          <img
            src={country.photo_url}
            alt={country.name}
            className="absolute inset-0 w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-black/40" />
        </>
      )}

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center justify-center h-full text-white">
        <h1 className="text-6xl font-bold mb-4">{country.name}</h1>

        {country.capital && (
          <p className="text-2xl mb-6">{country.capital[0]}</p>
        )}

        <button className="px-8 py-3 bg-blue-600 rounded-lg hover:bg-blue-700">
          Explorer cette destination
        </button>
      </div>

      {/* Photo credit */}
      {country.photo_credit && (
        <div className="absolute bottom-4 right-4 text-white/70 text-sm">
          <a
            href={country.photo_source || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:underline"
          >
            {country.photo_credit}
          </a>
        </div>
      )}
    </div>
  );
};
```

## 4. Grille de Pays avec Images

```tsx
// components/CountriesGrid.tsx
interface CountriesGridProps {
  countries: Country[];
}

export const CountriesGrid: React.FC<CountriesGridProps> = ({ countries }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
      {countries.map((country) => (
        <CountryCard key={country.code_iso2} country={country} />
      ))}
    </div>
  );
};
```

## 5. Optimisation des Images

### Utilisation de next/image (Next.js)

```tsx
import Image from 'next/image';

export const CountryCard: React.FC<CountryCardProps> = ({ country }) => {
  return (
    <div className="relative h-64 overflow-hidden rounded-lg">
      {country.photo_url && (
        <Image
          src={country.photo_url}
          alt={country.name}
          fill
          className="object-cover"
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          priority={false} // Lazy loading
        />
      )}
    </div>
  );
};
```

### Fallback si pas de photo

```tsx
export const CountryCard: React.FC<CountryCardProps> = ({ country }) => {
  const hasPhoto = country.photo_url;

  return (
    <div className="relative overflow-hidden rounded-lg">
      {hasPhoto ? (
        <img
          src={country.photo_url}
          alt={country.name}
          className="w-full h-64 object-cover"
        />
      ) : (
        // Fallback : utiliser le drapeau ou une couleur
        <div className="w-full h-64 bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center">
          {country.flags?.png && (
            <img
              src={country.flags.png}
              alt={`Drapeau ${country.name}`}
              className="w-32 h-32 object-contain"
            />
          )}
        </div>
      )}

      {/* Contenu... */}
    </div>
  );
};
```

## 6. Appel API depuis le Frontend

```typescript
// api/countries.ts
export async function getCountries(): Promise<Country[]> {
  const response = await fetch('https://votre-api.com/api/countries');

  if (!response.ok) {
    throw new Error('Failed to fetch countries');
  }

  return response.json();
}

// Usage dans un composant
import { useEffect, useState } from 'react';

export const CountriesPage = () => {
  const [countries, setCountries] = useState<Country[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCountries()
      .then(setCountries)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Chargement...</div>;

  return <CountriesGrid countries={countries} />;
};
```

## 7. Respect de la Licence Unsplash

**IMPORTANT** : Vous devez toujours afficher l'attribution. Voici un composant réutilisable :

```tsx
// components/PhotoCredit.tsx
interface PhotoCreditProps {
  credit?: string;
  source?: string;
  className?: string;
}

export const PhotoCredit: React.FC<PhotoCreditProps> = ({
  credit,
  source,
  className = "text-xs text-white/70"
}) => {
  if (!credit) return null;

  return (
    <p className={className}>
      {source ? (
        <a
          href={source}
          target="_blank"
          rel="noopener noreferrer"
          className="hover:underline"
        >
          {credit}
        </a>
      ) : (
        credit
      )}
    </p>
  );
};

// Usage
<PhotoCredit
  credit={country.photo_credit}
  source={country.photo_source}
/>
```

## 8. Exemple Complet : Page de Destination

```tsx
// pages/destinations/[countryCode].tsx
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import { CountryHero } from '@/components/CountryHero';

export default function CountryPage() {
  const router = useRouter();
  const { countryCode } = router.query;
  const [country, setCountry] = useState<Country | null>(null);

  useEffect(() => {
    if (countryCode) {
      fetch(`/api/countries/${countryCode}`)
        .then(res => res.json())
        .then(setCountry);
    }
  }, [countryCode]);

  if (!country) return <div>Chargement...</div>;

  return (
    <div>
      {/* Hero avec photo */}
      <CountryHero country={country} />

      {/* Contenu de la page */}
      <div className="container mx-auto py-12">
        <h2 className="text-3xl font-bold mb-6">
          Découvrir {country.name}
        </h2>

        <div className="grid md:grid-cols-2 gap-8">
          <div>
            <h3>Informations générales</h3>
            <ul>
              <li>Capitale: {country.capital?.[0]}</li>
              <li>Région: {country.region}</li>
              <li>Population: {country.population?.toLocaleString()}</li>
            </ul>
          </div>

          {country.daily_budget_min && (
            <div>
              <h3>Budget quotidien estimé</h3>
              <p>
                ${country.daily_budget_min} - ${country.daily_budget_max}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

## 9. Performance : Lazy Loading

```tsx
import { LazyLoadImage } from 'react-lazy-load-image-component';
import 'react-lazy-load-image-component/src/effects/blur.css';

export const CountryCard: React.FC<CountryCardProps> = ({ country }) => {
  return (
    <div className="country-card">
      {country.photo_url && (
        <LazyLoadImage
          src={country.photo_url}
          alt={country.name}
          effect="blur"
          className="country-image"
        />
      )}
    </div>
  );
};
```

## 10. SEO : Métadonnées avec Photo

```tsx
// pages/destinations/[countryCode].tsx
import Head from 'next/head';

export default function CountryPage({ country }: { country: Country }) {
  return (
    <>
      <Head>
        <title>{country.name} - Travliaq</title>
        <meta
          name="description"
          content={`Découvrez ${country.name} avec Travliaq`}
        />

        {/* Open Graph (Facebook, LinkedIn) */}
        <meta property="og:title" content={country.name} />
        <meta property="og:image" content={country.photo_url} />

        {/* Twitter Card */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:image" content={country.photo_url} />
      </Head>

      <CountryHero country={country} />
    </>
  );
}
```

---

## Résumé

✅ Toujours afficher `photo_credit` et `photo_source`
✅ Utiliser `loading="lazy"` pour les performances
✅ Prévoir un fallback si pas de photo
✅ Optimiser avec Next.js Image ou lazy loading
✅ Ajouter les métadonnées OG pour le SEO

**Bon développement ! 🚀**
