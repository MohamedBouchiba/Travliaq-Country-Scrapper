from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class Country(BaseModel):
    name: str
    code_iso2: str = Field(..., min_length=2, max_length=2)
    code_iso3: Optional[str] = Field(None, min_length=3, max_length=3)
    capital: Optional[List[str]] = None
    region: Optional[str] = None
    subregion: Optional[str] = None
    languages: Optional[Dict[str, str]] = None
    currencies: Optional[Dict[str, Any]] = None
    population: Optional[int] = None
    continents: Optional[List[str]] = None
    flags: Optional[Dict[str, str]] = None

    # Illustration photos (2 high-quality images for comparison)
    photo_url_1: Optional[str] = None
    photo_credit_1: Optional[str] = None
    photo_source_1: Optional[str] = None

    photo_url_2: Optional[str] = None
    photo_credit_2: Optional[str] = None
    photo_source_2: Optional[str] = None

    # Legacy single photo fields (kept for backwards compatibility)
    photo_url: Optional[str] = None
    photo_credit: Optional[str] = None
    photo_source: Optional[str] = None

    # Budget information (mid-range daily budget in USD)
    daily_budget_min: Optional[float] = None
    daily_budget_max: Optional[float] = None

    # Metadata
    source: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Future extensibility
    travel_info: Optional[Dict[str, Any]] = None

class City(BaseModel):
    name: str
    country_code: str # ISO2
    country_name: Optional[str] = None
    state_code: Optional[str] = None
    state_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    population: Optional[int] = None
    
    # Metadata
    source: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Travel Info (Enrichment)
    travel_info: Optional[Dict[str, Any]] = None # Summary, safety, etc.
    pois: Optional[List[Dict[str, Any]]] = None # Points of Interest
