from abc import ABC, abstractmethod
from typing import List
from src.models import Country, City

class BaseScraper(ABC):
    @abstractmethod
    def fetch_countries(self) -> List[Country]:
        """Fetch and return a list of Country objects."""
        pass

    @abstractmethod
    def fetch_cities(self) -> List[City]:
        """Fetch and return a list of City objects."""
        pass
