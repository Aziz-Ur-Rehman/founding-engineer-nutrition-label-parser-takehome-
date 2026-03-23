import csv
import logging
from pathlib import Path

from source_code.models import PipelineRow

logger = logging.getLogger(__name__)

FIELDNAMES = [
    "product_image",
    "serving_size",
    "parse_status",
    "nutrient_name_raw",
    "nutrient_name_standard",
    "amount",
    "unit",
    "original_amount",
    "original_unit",
    "daily_value_pct",
]


def write_csv(rows: list[PipelineRow], output_path: Path) -> None:
    """Write pipeline rows to CSV. Creates parent directories if needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows([row.to_dict() for row in rows])

    logger.info(f"{len(rows)} rows written to {output_path}")