from pymongo import MongoClient, UpdateOne
from pymongo.errors import ConnectionFailure
from src.config import settings
from src.models import Country, City
import logging
from typing import List

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.countries = None
        self.cities = None

    def connect(self):
        try:
            import certifi
            # Configure TLS with certifi and allow invalid certificates to bypass handshake errors
            self.client = MongoClient(
                settings.MONGODB_URI,
                tlsCAFile=certifi.where(),
                tls=True,
                tlsAllowInvalidCertificates=True,
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000
            )
            # Verify connection
            self.client.admin.command('ping')
            self.db = self.client[settings.DB_NAME]
            self.countries = self.db[settings.COUNTRY_COLLECTION]
            self.cities = self.db[settings.CITY_COLLECTION]
            
            # Create indexes
            self.countries.create_index("code_iso2", unique=True)
            self.cities.create_index([("name", 1), ("country_code", 1)], unique=True)
            
            logger.info("Successfully connected to MongoDB")
        except ConnectionFailure as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise

    def upsert_countries(self, countries: List[Country]):
        if not countries:
            return
            
        operations = []
        for country in countries:
            operations.append(
                UpdateOne(
                    {"code_iso2": country.code_iso2},
                    {"$set": country.model_dump()},
                    upsert=True
                )
            )
        
        if operations:
            result = self.countries.bulk_write(operations)
            logger.info(f"Upserted {len(countries)} countries. Modified: {result.modified_count}, Upserted: {result.upserted_count}")

    def upsert_cities(self, cities: List[City]):
        if not cities:
            return

        operations = []
        for city in cities:
            operations.append(
                UpdateOne(
                    {"name": city.name, "country_code": city.country_code},
                    {"$set": city.model_dump()},
                    upsert=True
                )
            )
            
        if operations:
            result = self.cities.bulk_write(operations)
            logger.info(f"Upserted {len(cities)} cities. Modified: {result.modified_count}, Upserted: {result.upserted_count}")

    def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
