"""LLM-based budget estimation for missing or outlier values."""
import os
import logging
import asyncio
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load .env from parent directories
env_paths = [
    Path(__file__).parent.parent.parent / ".env",  # Travliaq-Country-Scrapper/.env
    Path(__file__).parent.parent.parent.parent / "crewtravliaq" / ".env",  # crewtravliaq/.env
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)

logger = logging.getLogger(__name__)

# Budget thresholds for outlier detection
MIN_REASONABLE_BUDGET = 10.0   # Minimum reasonable daily budget
MAX_REASONABLE_BUDGET = 400.0  # Maximum reasonable (excluding luxury destinations)

# Prompt for budget estimation
ESTIMATION_PROMPT = """Tu es un expert en coût de la vie et voyage international.
Estime le budget journalier mid-range (USD) pour un voyageur dans ce pays.

Pays: {country_name}
Région: {region}
Pays voisins avec budgets connus: {neighbors}
Indice Numbeo (si disponible): {numbeo_index}

Le budget mid-range inclut:
- Hôtel 3 étoiles
- 3 repas/jour (restaurants locaux)
- Transport local
- 1-2 activités touristiques

IMPORTANT: Réponds UNIQUEMENT avec deux nombres séparés par une virgule.
Le premier est le budget MINIMUM, le second est le budget MAXIMUM.
Format: min,max
Exemple: 65,95

Ne mets pas de symbole dollar, juste les nombres."""

# Prompt for correcting outliers
CORRECTION_PROMPT = """Tu es un expert en coût de la vie et voyage international.
La valeur suivante semble être une erreur dans nos données:

Pays: {country_name}
Région: {region}
Valeur actuelle: ${current_value}/jour (probablement erronée)
Pays voisins avec budgets connus: {neighbors}
Indice Numbeo: {numbeo_index}

Cette valeur semble {issue}.

Estime le budget journalier mid-range RÉEL pour ce pays.

Le budget mid-range inclut:
- Hôtel 3 étoiles
- 3 repas/jour (restaurants locaux)
- Transport local
- 1-2 activités touristiques

IMPORTANT: Réponds UNIQUEMENT avec deux nombres séparés par une virgule.
Le premier est le budget MINIMUM, le second est le budget MAXIMUM.
Format: min,max
Exemple: 45,70

Ne mets pas de symbole dollar, juste les nombres."""


def is_outlier(budget: float) -> bool:
    """Check if a budget value is an outlier."""
    return budget < MIN_REASONABLE_BUDGET or budget > MAX_REASONABLE_BUDGET


def get_outlier_issue(budget: float) -> str:
    """Get description of the outlier issue."""
    if budget < MIN_REASONABLE_BUDGET:
        return "trop basse (possible erreur de conversion de devise ou données obsolètes)"
    elif budget > MAX_REASONABLE_BUDGET:
        return "trop élevée (possible erreur de saisie ou données corrompues)"
    return ""


async def estimate_budget_llm(
    country_name: str,
    region: str,
    neighbors_budgets: Dict[str, Tuple[float, float]],
    numbeo_index: Optional[float] = None
) -> Tuple[float, float]:
    """
    Use GPT-4o-mini to estimate a reasonable budget range.

    Args:
        country_name: Name of the country
        region: Geographic region
        neighbors_budgets: Dict of neighbor ISO2 -> (min, max) budgets
        numbeo_index: Numbeo cost of living index if available

    Returns:
        Tuple of (min_budget, max_budget) in USD
    """
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    neighbors_str = ", ".join(
        f"{name}: ${min_b:.0f}-${max_b:.0f}"
        for name, (min_b, max_b) in neighbors_budgets.items()
    ) if neighbors_budgets else "Non disponibles"

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": ESTIMATION_PROMPT.format(
                    country_name=country_name,
                    region=region,
                    neighbors=neighbors_str,
                    numbeo_index=f"{numbeo_index:.1f}" if numbeo_index else "Non disponible"
                )
            }],
            temperature=0.3,
            max_tokens=30
        )

        result = response.choices[0].message.content.strip()
        parts = result.replace(" ", "").split(",")

        if len(parts) >= 2:
            min_budget = float(parts[0])
            max_budget = float(parts[1])
            # Ensure min <= max
            if min_budget > max_budget:
                min_budget, max_budget = max_budget, min_budget
            return (round(min_budget, 2), round(max_budget, 2))

        # If only one value, create a range
        single_value = float(parts[0])
        return (round(single_value * 0.8, 2), round(single_value * 1.2, 2))

    except Exception as e:
        logger.error(f"LLM estimation failed for {country_name}: {e}")
        raise


async def correct_outlier_llm(
    country_name: str,
    region: str,
    current_value: float,
    neighbors_budgets: Dict[str, Tuple[float, float]],
    numbeo_index: Optional[float] = None
) -> Tuple[float, float]:
    """
    Use GPT-4o-mini to correct an outlier budget value.

    Args:
        country_name: Name of the country
        region: Geographic region
        current_value: Current outlier value
        neighbors_budgets: Dict of neighbor ISO2 -> (min, max) budgets
        numbeo_index: Numbeo cost of living index if available

    Returns:
        Tuple of (min_budget, max_budget) in USD
    """
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    neighbors_str = ", ".join(
        f"{name}: ${min_b:.0f}-${max_b:.0f}"
        for name, (min_b, max_b) in neighbors_budgets.items()
    ) if neighbors_budgets else "Non disponibles"

    issue = get_outlier_issue(current_value)

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": CORRECTION_PROMPT.format(
                    country_name=country_name,
                    region=region,
                    current_value=f"{current_value:.2f}",
                    neighbors=neighbors_str,
                    numbeo_index=f"{numbeo_index:.1f}" if numbeo_index else "Non disponible",
                    issue=issue
                )
            }],
            temperature=0.3,
            max_tokens=30
        )

        result = response.choices[0].message.content.strip()
        parts = result.replace(" ", "").split(",")

        if len(parts) >= 2:
            min_budget = float(parts[0])
            max_budget = float(parts[1])
            if min_budget > max_budget:
                min_budget, max_budget = max_budget, min_budget
            return (round(min_budget, 2), round(max_budget, 2))

        single_value = float(parts[0])
        return (round(single_value * 0.8, 2), round(single_value * 1.2, 2))

    except Exception as e:
        logger.error(f"LLM correction failed for {country_name}: {e}")
        raise


async def batch_estimate_budgets(
    countries_to_estimate: List[Dict],
    known_budgets: Dict[str, Tuple[float, float]]
) -> Dict[str, Tuple[float, float]]:
    """
    Batch estimate budgets for multiple countries using LLM.

    Args:
        countries_to_estimate: List of dicts with country info
        known_budgets: Already calculated budgets for context

    Returns:
        Dict mapping ISO2 -> (min, max) budget
    """
    from src.utils.country_mapping import get_neighbors, get_country_name

    results = {}

    # Process in batches to avoid rate limits
    batch_size = 5
    for i in range(0, len(countries_to_estimate), batch_size):
        batch = countries_to_estimate[i:i + batch_size]

        tasks = []
        for country_info in batch:
            iso2 = country_info["iso2"]
            name = country_info["name"]
            region = country_info["region"]
            numbeo_index = country_info.get("numbeo_index")
            current_value = country_info.get("current_value")

            # Get neighbor budgets for context
            neighbor_codes = get_neighbors(iso2)
            neighbor_budgets = {}
            for nc in neighbor_codes:
                if nc in known_budgets:
                    neighbor_name = get_country_name(nc)
                    if neighbor_name:
                        neighbor_budgets[neighbor_name] = known_budgets[nc]

            if current_value is not None and is_outlier(current_value):
                # Correct outlier
                tasks.append((
                    iso2,
                    correct_outlier_llm(name, region, current_value, neighbor_budgets, numbeo_index)
                ))
            else:
                # Estimate from scratch
                tasks.append((
                    iso2,
                    estimate_budget_llm(name, region, neighbor_budgets, numbeo_index)
                ))

        # Execute batch
        for iso2, task in tasks:
            try:
                result = await task
                results[iso2] = result
                logger.info(f"LLM estimated {iso2}: ${result[0]:.0f}-${result[1]:.0f}/day")
            except Exception as e:
                logger.error(f"Failed to estimate {iso2}: {e}")

        # Small delay between batches to avoid rate limits
        if i + batch_size < len(countries_to_estimate):
            await asyncio.sleep(1)

    return results
