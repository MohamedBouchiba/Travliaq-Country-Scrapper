"""Country name to ISO2 code mapping utilities."""
import logging
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

# Complete mapping from CSV country names to ISO2 codes
COUNTRY_NAME_TO_ISO2: Dict[str, str] = {
    # A
    "Afghanistan": "AF",
    "Albania": "AL",
    "Algeria": "DZ",
    "American Samoa": "AS",
    "Andorra": "AD",
    "Angola": "AO",
    "Anguilla": "AI",
    "Antarctica": "AQ",
    "Antigua and Barbuda": "AG",
    "Argentina": "AR",
    "Armenia": "AM",
    "Aruba": "AW",
    "Australia": "AU",
    "Austria": "AT",
    "Azerbaijan": "AZ",
    "Åland Islands": "AX",
    # B
    "Bahamas": "BS",
    "Bahrain": "BH",
    "Bangladesh": "BD",
    "Barbados": "BB",
    "Belarus": "BY",
    "Belgium": "BE",
    "Belize": "BZ",
    "Benin": "BJ",
    "Bermuda": "BM",
    "Bhutan": "BT",
    "Bolivia": "BO",
    "Bosnia and Herzegovina": "BA",
    "Botswana": "BW",
    "Bouvet Island": "BV",
    "Brazil": "BR",
    "British Indian Ocean Territory": "IO",
    "British Virgin Islands": "VG",
    "Brunei": "BN",
    "Bulgaria": "BG",
    "Burkina Faso": "BF",
    "Burundi": "BI",
    # C
    "Cambodia": "KH",
    "Cameroon": "CM",
    "Canada": "CA",
    "Cape Verde": "CV",
    "Caribbean Netherlands": "BQ",
    "Cayman Islands": "KY",
    "Central African Republic": "CF",
    "Chad": "TD",
    "Chile": "CL",
    "China": "CN",
    "Christmas Island": "CX",
    "Cocos (Keeling) Islands": "CC",
    "Colombia": "CO",
    "Comoros": "KM",
    "Cook Islands": "CK",
    "Costa Rica": "CR",
    "Croatia": "HR",
    "Cuba": "CU",
    "Curaçao": "CW",
    "Cyprus": "CY",
    "Czechia": "CZ",
    # D
    "Denmark": "DK",
    "Djibouti": "DJ",
    "Dominica": "DM",
    "Dominican Republic": "DO",
    "DR Congo": "CD",
    # E
    "Ecuador": "EC",
    "Egypt": "EG",
    "El Salvador": "SV",
    "Equatorial Guinea": "GQ",
    "Eritrea": "ER",
    "Estonia": "EE",
    "Eswatini": "SZ",
    "Ethiopia": "ET",
    # F
    "Falkland Islands": "FK",
    "Faroe Islands": "FO",
    "Fiji": "FJ",
    "Finland": "FI",
    "France": "FR",
    "French Guiana": "GF",
    "French Polynesia": "PF",
    "French Southern and Antarctic Lands": "TF",
    # G
    "Gabon": "GA",
    "Gambia": "GM",
    "Georgia": "GE",
    "Germany": "DE",
    "Ghana": "GH",
    "Gibraltar": "GI",
    "Greece": "GR",
    "Greenland": "GL",
    "Grenada": "GD",
    "Guadeloupe": "GP",
    "Guam": "GU",
    "Guatemala": "GT",
    "Guernsey": "GG",
    "Guinea": "GN",
    "Guinea-Bissau": "GW",
    "Guyana": "GY",
    # H
    "Haiti": "HT",
    "Heard Island and McDonald Islands": "HM",
    "Honduras": "HN",
    "Hong Kong": "HK",
    "Hungary": "HU",
    # I
    "Iceland": "IS",
    "India": "IN",
    "Indonesia": "ID",
    "Iran": "IR",
    "Iraq": "IQ",
    "Ireland": "IE",
    "Isle of Man": "IM",
    "Israel": "IL",
    "Italy": "IT",
    "Ivory Coast": "CI",
    # J
    "Jamaica": "JM",
    "Japan": "JP",
    "Jersey": "JE",
    "Jordan": "JO",
    # K
    "Kazakhstan": "KZ",
    "Kenya": "KE",
    "Kiribati": "KI",
    "Kosovo": "XK",
    "Kuwait": "KW",
    "Kyrgyzstan": "KG",
    # L
    "Laos": "LA",
    "Latvia": "LV",
    "Lebanon": "LB",
    "Lesotho": "LS",
    "Liberia": "LR",
    "Libya": "LY",
    "Liechtenstein": "LI",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    # M
    "Macau": "MO",
    "Madagascar": "MG",
    "Malawi": "MW",
    "Malaysia": "MY",
    "Maldives": "MV",
    "Mali": "ML",
    "Malta": "MT",
    "Marshall Islands": "MH",
    "Martinique": "MQ",
    "Mauritania": "MR",
    "Mauritius": "MU",
    "Mayotte": "YT",
    "Mexico": "MX",
    "Micronesia": "FM",
    "Moldova": "MD",
    "Monaco": "MC",
    "Mongolia": "MN",
    "Montenegro": "ME",
    "Montserrat": "MS",
    "Morocco": "MA",
    "Mozambique": "MZ",
    "Myanmar": "MM",
    # N
    "Namibia": "NA",
    "Nauru": "NR",
    "Nepal": "NP",
    "Netherlands": "NL",
    "New Caledonia": "NC",
    "New Zealand": "NZ",
    "Nicaragua": "NI",
    "Niger": "NE",
    "Nigeria": "NG",
    "Niue": "NU",
    "Norfolk Island": "NF",
    "North Korea": "KP",
    "North Macedonia": "MK",
    "Northern Mariana Islands": "MP",
    "Norway": "NO",
    # O
    "Oman": "OM",
    # P
    "Pakistan": "PK",
    "Palau": "PW",
    "Palestine": "PS",
    "Panama": "PA",
    "Papua New Guinea": "PG",
    "Paraguay": "PY",
    "Peru": "PE",
    "Philippines": "PH",
    "Pitcairn Islands": "PN",
    "Poland": "PL",
    "Portugal": "PT",
    "Puerto Rico": "PR",
    # Q
    "Qatar": "QA",
    # R
    "Republic of the Congo": "CG",
    "Romania": "RO",
    "Russia": "RU",
    "Rwanda": "RW",
    "Réunion": "RE",
    # S
    "Saint Barthélemy": "BL",
    "Saint Helena, Ascension and Tristan da Cunha": "SH",
    "Saint Kitts and Nevis": "KN",
    "Saint Lucia": "LC",
    "Saint Martin": "MF",
    "Saint Pierre and Miquelon": "PM",
    "Saint Vincent and the Grenadines": "VC",
    "Samoa": "WS",
    "San Marino": "SM",
    "Saudi Arabia": "SA",
    "Senegal": "SN",
    "Serbia": "RS",
    "Seychelles": "SC",
    "Sierra Leone": "SL",
    "Singapore": "SG",
    "Sint Maarten": "SX",
    "Slovakia": "SK",
    "Slovenia": "SI",
    "Solomon Islands": "SB",
    "Somalia": "SO",
    "South Africa": "ZA",
    "South Georgia": "GS",
    "South Korea": "KR",
    "South Sudan": "SS",
    "Spain": "ES",
    "Sri Lanka": "LK",
    "Sudan": "SD",
    "Suriname": "SR",
    "Svalbard and Jan Mayen": "SJ",
    "Sweden": "SE",
    "Switzerland": "CH",
    "Syria": "SY",
    "São Tomé and Príncipe": "ST",
    # T
    "Taiwan": "TW",
    "Tajikistan": "TJ",
    "Tanzania": "TZ",
    "Thailand": "TH",
    "Timor-Leste": "TL",
    "Togo": "TG",
    "Tokelau": "TK",
    "Tonga": "TO",
    "Trinidad and Tobago": "TT",
    "Tunisia": "TN",
    "Turkey": "TR",
    "Turkmenistan": "TM",
    "Turks and Caicos Islands": "TC",
    "Tuvalu": "TV",
    # U
    "Uganda": "UG",
    "Ukraine": "UA",
    "United Arab Emirates": "AE",
    "United Kingdom": "GB",
    "United States": "US",
    "United States Minor Outlying Islands": "UM",
    "United States Virgin Islands": "VI",
    "Uruguay": "UY",
    "Uzbekistan": "UZ",
    # V
    "Vanuatu": "VU",
    "Vatican City": "VA",
    "Venezuela": "VE",
    "Vietnam": "VN",
    # W
    "Wallis and Futuna": "WF",
    "Western Sahara": "EH",
    # Y
    "Yemen": "YE",
    # Z
    "Zambia": "ZM",
    "Zimbabwe": "ZW",
}

# Reverse mapping: ISO2 to country name
ISO2_TO_COUNTRY_NAME: Dict[str, str] = {v: k for k, v in COUNTRY_NAME_TO_ISO2.items()}

# Region mapping for LLM context
COUNTRY_REGIONS: Dict[str, str] = {
    # Africa
    "DZ": "North Africa", "AO": "Central Africa", "BJ": "West Africa",
    "BW": "Southern Africa", "BF": "West Africa", "BI": "East Africa",
    "CV": "West Africa", "CM": "Central Africa", "CF": "Central Africa",
    "TD": "Central Africa", "KM": "East Africa", "CD": "Central Africa",
    "CG": "Central Africa", "DJ": "East Africa", "EG": "North Africa",
    "GQ": "Central Africa", "ER": "East Africa", "SZ": "Southern Africa",
    "ET": "East Africa", "GA": "Central Africa", "GM": "West Africa",
    "GH": "West Africa", "GN": "West Africa", "GW": "West Africa",
    "CI": "West Africa", "KE": "East Africa", "LS": "Southern Africa",
    "LR": "West Africa", "LY": "North Africa", "MG": "East Africa",
    "MW": "East Africa", "ML": "West Africa", "MR": "West Africa",
    "MU": "East Africa", "MA": "North Africa", "MZ": "East Africa",
    "NA": "Southern Africa", "NE": "West Africa", "NG": "West Africa",
    "RW": "East Africa", "ST": "Central Africa", "SN": "West Africa",
    "SC": "East Africa", "SL": "West Africa", "SO": "East Africa",
    "ZA": "Southern Africa", "SS": "East Africa", "SD": "North Africa",
    "TZ": "East Africa", "TG": "West Africa", "TN": "North Africa",
    "UG": "East Africa", "ZM": "Southern Africa", "ZW": "Southern Africa",
    "RE": "East Africa", "YT": "East Africa", "EH": "North Africa",
    # Europe
    "AL": "Southern Europe", "AD": "Western Europe", "AT": "Western Europe",
    "BY": "Eastern Europe", "BE": "Western Europe", "BA": "Southern Europe",
    "BG": "Eastern Europe", "HR": "Southern Europe", "CY": "Southern Europe",
    "CZ": "Central Europe", "DK": "Northern Europe", "EE": "Northern Europe",
    "FI": "Northern Europe", "FR": "Western Europe", "DE": "Western Europe",
    "GR": "Southern Europe", "HU": "Central Europe", "IS": "Northern Europe",
    "IE": "Western Europe", "IT": "Southern Europe", "XK": "Southern Europe",
    "LV": "Northern Europe", "LI": "Western Europe", "LT": "Northern Europe",
    "LU": "Western Europe", "MT": "Southern Europe", "MD": "Eastern Europe",
    "MC": "Western Europe", "ME": "Southern Europe", "NL": "Western Europe",
    "MK": "Southern Europe", "NO": "Northern Europe", "PL": "Central Europe",
    "PT": "Southern Europe", "RO": "Eastern Europe", "RU": "Eastern Europe",
    "SM": "Southern Europe", "RS": "Southern Europe", "SK": "Central Europe",
    "SI": "Southern Europe", "ES": "Southern Europe", "SE": "Northern Europe",
    "CH": "Western Europe", "UA": "Eastern Europe", "GB": "Western Europe",
    "VA": "Southern Europe", "GI": "Southern Europe", "GG": "Western Europe",
    "IM": "Western Europe", "JE": "Western Europe", "FO": "Northern Europe",
    "AX": "Northern Europe", "SJ": "Northern Europe",
    # Asia
    "AF": "Central Asia", "AM": "Western Asia", "AZ": "Western Asia",
    "BH": "Western Asia", "BD": "South Asia", "BT": "South Asia",
    "BN": "Southeast Asia", "KH": "Southeast Asia", "CN": "East Asia",
    "GE": "Western Asia", "HK": "East Asia", "IN": "South Asia",
    "ID": "Southeast Asia", "IR": "Western Asia", "IQ": "Western Asia",
    "IL": "Western Asia", "JP": "East Asia", "JO": "Western Asia",
    "KZ": "Central Asia", "KW": "Western Asia", "KG": "Central Asia",
    "LA": "Southeast Asia", "LB": "Western Asia", "MO": "East Asia",
    "MY": "Southeast Asia", "MV": "South Asia", "MN": "East Asia",
    "MM": "Southeast Asia", "NP": "South Asia", "KP": "East Asia",
    "OM": "Western Asia", "PK": "South Asia", "PS": "Western Asia",
    "PH": "Southeast Asia", "QA": "Western Asia", "SA": "Western Asia",
    "SG": "Southeast Asia", "KR": "East Asia", "LK": "South Asia",
    "SY": "Western Asia", "TW": "East Asia", "TJ": "Central Asia",
    "TH": "Southeast Asia", "TL": "Southeast Asia", "TR": "Western Asia",
    "TM": "Central Asia", "AE": "Western Asia", "UZ": "Central Asia",
    "VN": "Southeast Asia", "YE": "Western Asia",
    # North America
    "AG": "Caribbean", "BS": "Caribbean", "BB": "Caribbean",
    "BZ": "Central America", "CA": "North America", "CR": "Central America",
    "CU": "Caribbean", "DM": "Caribbean", "DO": "Caribbean",
    "SV": "Central America", "GD": "Caribbean", "GT": "Central America",
    "HT": "Caribbean", "HN": "Central America", "JM": "Caribbean",
    "MX": "North America", "NI": "Central America", "PA": "Central America",
    "KN": "Caribbean", "LC": "Caribbean", "VC": "Caribbean",
    "TT": "Caribbean", "US": "North America", "AI": "Caribbean",
    "AW": "Caribbean", "BM": "North America", "BQ": "Caribbean",
    "VG": "Caribbean", "KY": "Caribbean", "CW": "Caribbean",
    "GL": "North America", "GP": "Caribbean", "MQ": "Caribbean",
    "MS": "Caribbean", "PR": "Caribbean", "BL": "Caribbean",
    "MF": "Caribbean", "PM": "North America", "SX": "Caribbean",
    "TC": "Caribbean", "VI": "Caribbean",
    # South America
    "AR": "South America", "BO": "South America", "BR": "South America",
    "CL": "South America", "CO": "South America", "EC": "South America",
    "FK": "South America", "GF": "South America", "GY": "South America",
    "PY": "South America", "PE": "South America", "SR": "South America",
    "UY": "South America", "VE": "South America",
    # Oceania
    "AS": "Polynesia", "AU": "Australia", "CK": "Polynesia",
    "FJ": "Melanesia", "PF": "Polynesia", "GU": "Micronesia",
    "KI": "Micronesia", "MH": "Micronesia", "FM": "Micronesia",
    "NR": "Micronesia", "NC": "Melanesia", "NZ": "Australia",
    "NU": "Polynesia", "NF": "Australia", "MP": "Micronesia",
    "PW": "Micronesia", "PG": "Melanesia", "PN": "Polynesia",
    "WS": "Polynesia", "SB": "Melanesia", "TK": "Polynesia",
    "TO": "Polynesia", "TV": "Polynesia", "VU": "Melanesia",
    "WF": "Polynesia",
    # Special
    "AQ": "Antarctica", "BV": "Antarctica", "TF": "Antarctica",
    "GS": "Antarctica", "HM": "Antarctica", "IO": "Indian Ocean",
    "CX": "Indian Ocean", "CC": "Indian Ocean", "UM": "Pacific Ocean",
}

# Neighboring countries for LLM context
COUNTRY_NEIGHBORS: Dict[str, list] = {
    "FR": ["DE", "BE", "LU", "CH", "IT", "ES", "AD", "MC"],
    "DE": ["FR", "BE", "NL", "LU", "CH", "AT", "CZ", "PL", "DK"],
    "ES": ["FR", "PT", "AD", "MA"],
    "IT": ["FR", "CH", "AT", "SI", "VA", "SM"],
    "US": ["CA", "MX"],
    "CN": ["RU", "MN", "KP", "VN", "LA", "MM", "IN", "BT", "NP", "PK", "AF", "TJ", "KG", "KZ"],
    "RU": ["NO", "FI", "EE", "LV", "BY", "UA", "GE", "AZ", "KZ", "CN", "MN", "KP"],
    "BR": ["AR", "UY", "PY", "BO", "PE", "CO", "VE", "GY", "SR", "GF"],
    "IN": ["PK", "CN", "NP", "BT", "BD", "MM"],
    "AU": ["NZ", "ID", "PG"],
    "JP": ["KR", "CN", "TW", "RU"],
    "GB": ["IE", "FR"],
    "MX": ["US", "GT", "BZ"],
    "TH": ["MM", "LA", "KH", "MY"],
    "VN": ["CN", "LA", "KH"],
    "EG": ["LY", "SD", "IL", "PS"],
    "ZA": ["NA", "BW", "ZW", "MZ", "SZ", "LS"],
    "TR": ["GR", "BG", "GE", "AM", "AZ", "IR", "IQ", "SY"],
    "SA": ["JO", "IQ", "KW", "BH", "QA", "AE", "OM", "YE"],
    "PL": ["DE", "CZ", "SK", "UA", "BY", "LT", "RU"],
    "AR": ["CL", "BO", "PY", "BR", "UY"],
    "DZ": ["MA", "TN", "LY", "NE", "ML", "MR"],
    "MA": ["DZ", "EH", "ES"],
    "ID": ["MY", "PG", "TL", "AU"],
    "PH": ["TW", "MY", "ID", "VN"],
    "KR": ["KP", "JP"],
    "VE": ["CO", "BR", "GY"],
    "CO": ["VE", "BR", "PE", "EC", "PA"],
    "PE": ["EC", "CO", "BR", "BO", "CL"],
    "CL": ["PE", "BO", "AR"],
    "PK": ["IN", "CN", "AF", "IR"],
    "BD": ["IN", "MM"],
    "NG": ["BJ", "NE", "TD", "CM"],
    "ET": ["ER", "DJ", "SO", "KE", "SS", "SD"],
    "KE": ["ET", "SO", "TZ", "UG", "SS"],
    "TZ": ["KE", "UG", "RW", "BI", "CD", "ZM", "MW", "MZ"],
    "UA": ["RU", "BY", "PL", "SK", "HU", "RO", "MD"],
    "IR": ["IQ", "TR", "AM", "AZ", "TM", "AF", "PK"],
    "IQ": ["IR", "TR", "SY", "JO", "SA", "KW"],
    "SY": ["TR", "IQ", "JO", "IL", "LB"],
    "AF": ["PK", "IR", "TM", "UZ", "TJ", "CN"],
}


def get_iso2_from_name(country_name: str) -> Optional[str]:
    """
    Get ISO2 code from country name.

    Args:
        country_name: Country name from CSV

    Returns:
        ISO2 code or None if not found
    """
    if not country_name:
        return None

    name = country_name.strip()

    # Direct lookup
    if name in COUNTRY_NAME_TO_ISO2:
        return COUNTRY_NAME_TO_ISO2[name]

    # Try pycountry as fallback
    try:
        import pycountry

        # Exact name match
        country = pycountry.countries.get(name=name)
        if country:
            return country.alpha_2

        # Common name match
        try:
            country = pycountry.countries.get(common_name=name)
            if country:
                return country.alpha_2
        except (KeyError, LookupError):
            pass

        # Fuzzy search
        try:
            results = pycountry.countries.search_fuzzy(name)
            if results:
                return results[0].alpha_2
        except LookupError:
            pass

    except ImportError:
        logger.debug("pycountry not installed, using static mapping only")
    except Exception as e:
        logger.debug(f"pycountry lookup failed for {name}: {e}")

    logger.warning(f"Could not find ISO2 code for country: {name}")
    return None


def get_country_name(iso2: str) -> Optional[str]:
    """Get country name from ISO2 code."""
    return ISO2_TO_COUNTRY_NAME.get(iso2.upper())


def get_region(iso2: str) -> str:
    """Get region for a country."""
    return COUNTRY_REGIONS.get(iso2.upper(), "Unknown")


def get_neighbors(iso2: str) -> list:
    """Get neighboring countries for a country."""
    return COUNTRY_NEIGHBORS.get(iso2.upper(), [])
