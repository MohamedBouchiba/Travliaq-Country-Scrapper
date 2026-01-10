"""USD cost parsing utilities for BudgetYourTrip data."""
import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def parse_usd_value(value: str) -> Optional[float]:
    """
    Parse USD value from BudgetYourTrip format.

    Formats handled:
    - "$81(EUR69)" -> 81.0
    - "$44(AR$64,377)" -> 44.0
    - "$0.00(Ʈ79)" -> None (zero = missing)
    - "$131" -> 131.0
    - "" -> None

    Args:
        value: Raw string from CSV

    Returns:
        Parsed USD float or None if invalid/missing
    """
    if not value or not isinstance(value, str):
        return None

    value = value.strip()
    if not value or not value.startswith('$'):
        return None

    # Match: $<digits with optional comma and decimal>
    match = re.match(r'\$([\d,]+\.?\d*)', value)
    if match:
        usd_str = match.group(1).replace(',', '')
        try:
            usd_value = float(usd_str)
            # Treat $0.00 as missing data (currency conversion failed)
            if usd_value < 0.01:
                return None
            return usd_value
        except ValueError:
            logger.warning(f"Could not parse USD value: {value}")
            return None

    return None


def parse_numbeo_index(value: str) -> Optional[float]:
    """
    Parse Numbeo index value.

    Args:
        value: Index value string from CSV

    Returns:
        Float index or None if invalid
    """
    if not value or not isinstance(value, str):
        return None

    value = value.strip()
    if not value:
        return None

    try:
        index = float(value)
        return index if index > 0 else None
    except (ValueError, TypeError):
        return None
