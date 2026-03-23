import re
import logging
from typing import Optional

from source_code.data.nutrient_map import NUTRIENT_MAP, IU_CONVERSION
from source_code.data.unit_map import UNIT_MAP
from source_code.models import RawNutrient, NormalizedNutrient

logger = logging.getLogger(__name__)


def _to_snake_case(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text


def normalize_nutrient_name(name_raw: str) -> str:
    key = name_raw.lower().strip()
    standard = NUTRIENT_MAP.get(key)
    if standard is None:
        standard = _to_snake_case(name_raw)
        logger.debug(f"Unmapped nutrient '{name_raw}' → '{standard}'")
    return standard


def normalize_unit(unit_raw: Optional[str]) -> Optional[str]:
    if not unit_raw:
        return None
    return UNIT_MAP.get(unit_raw.lower().strip(), unit_raw.lower().strip())


def _apply_iu_conversion(
    amount: Optional[float],
    unit: Optional[str],
    nutrient_standard: str,
) -> tuple[Optional[float], Optional[str]]:
    """Convert to IU for nutrients where this is standard and unambiguous."""
    if amount is None or unit is None:
        return amount, unit

    conversions = IU_CONVERSION.get(nutrient_standard, {})
    multiplier = conversions.get(unit)

    if multiplier is not None:
        return round(amount * multiplier, 4), "IU"

    return amount, unit


def normalize_nutrient(raw: RawNutrient) -> NormalizedNutrient:
    name_standard = normalize_nutrient_name(raw.name_raw)
    original_unit = normalize_unit(raw.unit)
    amount_converted, unit_converted = _apply_iu_conversion(
        raw.amount, original_unit, name_standard
    )

    return NormalizedNutrient(
        nutrient_name_raw=raw.name_raw,
        nutrient_name_standard=name_standard,
        amount=amount_converted,
        unit=unit_converted,
        original_amount=raw.amount,
        original_unit=original_unit,
        daily_value_pct=raw.daily_value_pct,
    )