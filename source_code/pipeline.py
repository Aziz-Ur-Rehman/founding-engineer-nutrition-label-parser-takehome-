import asyncio
import logging
import logging.handlers
from pathlib import Path

import anthropic

from source_code.config import config
from source_code.extractor import extract_nutrients_async
from source_code.normalizer import normalize_nutrient
from source_code.models import PipelineRow, ExtractionResult
from source_code.writer import write_csv

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.handlers.RotatingFileHandler(
        config.LOG_DIR / "pipeline.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler],
    )


def _get_image_paths(input_dir: Path) -> list[Path]:
    paths = sorted([
        p for p in input_dir.iterdir()
        if p.suffix.lower() in config.SUPPORTED_EXTENSIONS
    ])
    logger.info(f"Found {len(paths)} images in {input_dir}")
    return paths


def _build_rows(result: ExtractionResult) -> list[PipelineRow]:
    """Convert a single ExtractionResult into output rows."""
    if not result.has_data or not result.nutrients:
        return []

    rows = []
    for raw_nutrient in result.nutrients:
        normalized = normalize_nutrient(raw_nutrient)
        rows.append(PipelineRow(
            product_image=result.image_name,
            serving_size=result.serving_size,
            parse_status=result.parse_status,
            nutrient_name_raw=normalized.nutrient_name_raw,
            nutrient_name_standard=normalized.nutrient_name_standard,
            amount=normalized.amount,
            unit=normalized.unit,
            original_amount=normalized.original_amount,
            original_unit=normalized.original_unit,
            daily_value_pct=normalized.daily_value_pct,
        ))
    return rows


async def _run_pipeline_async(input_dir: Path, output_file: Path) -> None:
    config.validate()

    client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY)

    image_paths = _get_image_paths(input_dir)
    if not image_paths:
        logger.warning("No images found. Exiting.")
        return

    logger.info(
        f"Processing {len(image_paths)} images "
        f"with concurrency={config.MAX_CONCURRENCY}"
    )

    # Fire all images concurrently, semaphore controls rate
    tasks = [
        extract_nutrients_async(image_path, client, semaphore)
        for image_path in image_paths
    ]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    all_rows: list[PipelineRow] = []
    skipped = 0

    for result in results:
        rows = _build_rows(result)
        if rows:
            all_rows.extend(rows)
            logger.info(
                f"{result.image_name} → {len(rows)} nutrients extracted"
            )
        else:
            skipped += 1
            logger.info(
                f"{result.image_name} → skipped "
                f"(status: {result.parse_status})"
            )

    if not all_rows:
        logger.warning("No data extracted from any image.")
        return

    write_csv(all_rows, output_file)

    logger.info(
        f"Pipeline complete — "
        f"{len(all_rows)} rows from "
        f"{len(image_paths) - skipped}/{len(image_paths)} images"
    )


def run_pipeline(input_dir: Path, output_file: Path) -> None:
    _setup_logging()
    asyncio.run(_run_pipeline_async(input_dir, output_file))