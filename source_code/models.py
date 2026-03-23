from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RawNutrient:
    """Nutrient as returned by the extractor — no normalization applied."""
    name_raw: str
    amount: Optional[float]
    unit: Optional[str]
    daily_value_pct: Optional[float]


@dataclass
class NormalizedNutrient:
    """Nutrient after normalization — ready for CSV output."""
    nutrient_name_raw: str
    nutrient_name_standard: str
    amount: Optional[float]
    unit: Optional[str]
    original_amount: Optional[float]
    original_unit: Optional[str]
    daily_value_pct: Optional[float]


@dataclass
class ExtractionResult:
    """Full result for one image from the extractor."""
    image_name: str
    has_data: bool
    parse_status: str
    serving_size: Optional[str]
    nutrients: list[RawNutrient] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class PipelineRow:
    """One output row — one nutrient from one image."""
    product_image: str
    serving_size: Optional[str]
    parse_status: str
    nutrient_name_raw: str
    nutrient_name_standard: str
    amount: Optional[float]
    unit: Optional[str]
    original_amount: Optional[float]
    original_unit: Optional[str]
    daily_value_pct: Optional[float]

    def to_dict(self) -> dict:
        return {
            "product_image": self.product_image,
            "serving_size": self.serving_size,
            "parse_status": self.parse_status,
            "nutrient_name_raw": self.nutrient_name_raw,
            "nutrient_name_standard": self.nutrient_name_standard,
            "amount": self.amount,
            "unit": self.unit,
            "original_amount": self.original_amount,
            "original_unit": self.original_unit,
            "daily_value_pct": self.daily_value_pct,
        }