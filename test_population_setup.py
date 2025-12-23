#!/usr/bin/env python3
"""
Test script to verify environment setup for population enrichment.

Usage:
    python test_population_setup.py
"""

import os
import sys
from dotenv import load_dotenv

def check_import(module_name: str, package_name: str = None) -> bool:
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        print(f"[OK] {package_name or module_name} is installed")
        return True
    except ImportError:
        print(f"[FAIL] {package_name or module_name} is NOT installed")
        print(f"  Install with: pip install {package_name or module_name}")
        return False

def check_env_var(var_name: str, required: bool = True) -> bool:
    """Check if an environment variable is set."""
    value = os.getenv(var_name)
    if value:
        # Mask sensitive values
        if any(x in var_name.lower() for x in ['password', 'secret', 'key', 'token']):
            display_value = '*' * 8
        elif 'url' in var_name.lower() and '@' in value:
            # Mask DB URL password
            parts = value.split('@')
            display_value = parts[0].split(':')[0] + ':***@' + parts[1]
        else:
            display_value = value[:50] + '...' if len(value) > 50 else value

        print(f"[OK] {var_name} = {display_value}")
        return True
    else:
        status = "[FAIL]" if required else "[SKIP]"
        print(f"{status} {var_name} is not set")
        if required:
            print(f"  Required for the script to run")
        return not required

def test_database_connection() -> bool:
    """Test database connection."""
    db_url = os.getenv("SUPABASE_DB_URL")

    # If SUPABASE_DB_URL not provided, build from individual components
    if not db_url:
        pg_host = os.getenv("PG_HOST")
        pg_user = os.getenv("PG_USER")
        pg_password = os.getenv("PG_PASSWORD")
        pg_database = os.getenv("PG_DATABASE", "postgres")
        pg_port = os.getenv("PG_PORT", "5432")
        pg_sslmode = os.getenv("PG_SSLMODE", "require")

        if pg_host and pg_user and pg_password:
            from urllib.parse import quote_plus
            db_url = f"postgresql://{pg_user}:{quote_plus(pg_password)}@{pg_host}:{pg_port}/{pg_database}?sslmode={pg_sslmode}"
            print("[INFO] Using individual PG_* environment variables")
        else:
            print("[FAIL] Cannot test DB connection - missing database configuration")
            print("  Provide either SUPABASE_DB_URL or PG_HOST/PG_USER/PG_PASSWORD")
            return False

    try:
        import psycopg2
        print("\nTesting database connection...")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM public.cities WHERE location IS NOT NULL")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"[OK] Database connection successful")
        print(f"  Found {count:,} cities with location data")
        return True
    except Exception as e:
        print(f"[FAIL] Database connection failed: {e}")
        return False

def test_geonames_download() -> bool:
    """Test GeoNames download."""
    dataset = os.getenv("GEONAMES_DATASET", "cities15000")
    url = f"https://download.geonames.org/export/dump/{dataset}.zip"

    try:
        import requests
        print(f"\nTesting GeoNames download ({dataset})...")
        response = requests.head(url, timeout=10)

        if response.status_code == 200:
            size_mb = int(response.headers.get('Content-Length', 0)) / 1024 / 1024
            print(f"[OK] GeoNames dataset accessible")
            print(f"  Dataset: {dataset}")
            print(f"  Size: {size_mb:.1f} MB")
            return True
        else:
            print(f"[FAIL] GeoNames dataset not accessible (status: {response.status_code})")
            return False
    except Exception as e:
        print(f"[FAIL] GeoNames download test failed: {e}")
        return False

def main():
    """Run all checks."""
    print("=" * 60)
    print("POPULATION ENRICHMENT SETUP TEST")
    print("=" * 60)

    # Load .env
    load_dotenv()
    print("\n1. Environment Variables")
    print("-" * 60)

    # Check database configuration (either SUPABASE_DB_URL or PG_* variables)
    has_db_url = check_env_var("SUPABASE_DB_URL", required=False)

    if not has_db_url:
        print("\n  Alternative: Using individual PostgreSQL variables")
        pg_host_ok = check_env_var("PG_HOST", required=False)
        pg_user_ok = check_env_var("PG_USER", required=False)
        pg_password_ok = check_env_var("PG_PASSWORD", required=False)
        check_env_var("PG_DATABASE", required=False)
        check_env_var("PG_PORT", required=False)
        check_env_var("PG_SSLMODE", required=False)

        db_config_ok = pg_host_ok and pg_user_ok and pg_password_ok
        if not db_config_ok:
            print("\n  [WARN] Missing required PG_HOST, PG_USER, or PG_PASSWORD")
    else:
        db_config_ok = True

    # Optional configuration
    print("\n  Optional configuration:")
    check_env_var("GEONAMES_DATASET", required=False)
    check_env_var("MAX_RADIUS_KM", required=False)
    check_env_var("WIKIDATA_MAX_QPS", required=False)
    check_env_var("BATCH_SIZE", required=False)
    check_env_var("ONLY_NULL", required=False)

    # Check dependencies
    print("\n2. Python Dependencies")
    print("-" * 60)

    dep_checks = [
        check_import("psycopg2", "psycopg2-binary"),
        check_import("dotenv", "python-dotenv"),
        check_import("requests"),
        check_import("httpx"),
        check_import("rapidfuzz"),
        check_import("tenacity"),
        check_import("unidecode"),
        check_import("tqdm"),
    ]

    # Test database connection
    print("\n3. Database Connection")
    print("-" * 60)
    db_check = test_database_connection()

    # Test GeoNames
    print("\n4. GeoNames Access")
    print("-" * 60)
    geonames_check = test_geonames_download()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_required_ok = db_config_ok and all(dep_checks) and db_check

    if all_required_ok:
        print("[SUCCESS] All required checks passed!")
        print("\nYou can run the population enrichment script:")
        print("  python populate_population.py")
        print("\nOr directly:")
        print("  python src/migration/populate_city_population.py")
        return 0
    else:
        print("[FAIL] Some required checks failed")
        print("\nPlease fix the issues above before running the script.")
        print("\nQuick fixes:")
        print("  1. Copy .env.example to .env and fill in your credentials")
        print("  2. Install missing dependencies: pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
