-- Script SQL pour créer les tables countries et cities dans PostgreSQL/Supabase
-- Exécutez ce script dans le SQL Editor de Supabase avant de lancer la migration

-- ============================================================
-- Table: countries (Pays)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.countries (
  iso2 character(2) NOT NULL,
  iso3 character(3) NULL,
  name text NOT NULL,
  slug text NOT NULL,
  population bigint NULL,
  region text NULL,
  subregion text NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NULL,
  CONSTRAINT countries_pkey PRIMARY KEY (iso2)
) TABLESPACE pg_default;

-- Index unique sur le slug
CREATE UNIQUE INDEX IF NOT EXISTS countries_slug_uidx
  ON public.countries USING btree (slug)
  TABLESPACE pg_default;

-- Index sur le nom (recherche insensible à la casse)
CREATE INDEX IF NOT EXISTS countries_name_idx
  ON public.countries USING btree (lower(name))
  TABLESPACE pg_default;


-- ============================================================
-- Table: cities (Villes)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.cities (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  country text NOT NULL,
  country_code text NOT NULL,
  search_text text GENERATED ALWAYS AS (lower(((name || ', '::text) || country))) STORED NULL,
  created_at timestamp with time zone NULL DEFAULT now(),
  slug text NULL,
  latitude double precision NULL,
  longitude double precision NULL,
  location geography NULL,
  state_code text NULL,
  state_name text NULL,
  population bigint NULL,
  updated_at timestamp with time zone NULL,
  CONSTRAINT cities_pkey PRIMARY KEY (id)
) TABLESPACE pg_default;

-- Index unique sur (slug, country_code)
CREATE UNIQUE INDEX IF NOT EXISTS cities_slug_country_uidx
  ON public.cities USING btree (slug, country_code)
  TABLESPACE pg_default;

-- Index GIN pour la recherche full-text (nécessite l'extension pg_trgm)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_cities_search
  ON public.cities USING gin (search_text gin_trgm_ops)
  TABLESPACE pg_default;

-- Index sur le nom (recherche insensible à la casse)
CREATE INDEX IF NOT EXISTS idx_cities_name
  ON public.cities USING btree (lower(name))
  TABLESPACE pg_default;

-- Index sur le slug
CREATE INDEX IF NOT EXISTS cities_slug_idx
  ON public.cities USING btree (slug)
  TABLESPACE pg_default;

-- Index sur le country_code
CREATE INDEX IF NOT EXISTS cities_country_code_idx
  ON public.cities USING btree (country_code)
  TABLESPACE pg_default;

-- Index spatial GIST sur la localisation (nécessite PostGIS)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE INDEX IF NOT EXISTS cities_location_gix
  ON public.cities USING gist (location)
  TABLESPACE pg_default;


-- ============================================================
-- Vérification
-- ============================================================

-- Afficher les tables créées
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = 'public' AND table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_name IN ('countries', 'cities')
ORDER BY table_name;

-- Afficher les index créés
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('countries', 'cities')
ORDER BY tablename, indexname;
