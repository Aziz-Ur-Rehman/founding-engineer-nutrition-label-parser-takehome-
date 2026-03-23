import asyncio
import base64
import json
import logging
from pathlib import Path

import anthropic

from source_code.config import config
from source_code.models import ExtractionResult, RawNutrient

logger = logging.getLogger(__name__)


def _load_prompt() -> str:
    return config.PROMPT_PATH.read_text(encoding="utf-8")


def _load_image_as_base64(image_path: Path) -> tuple[str, str]:
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    media_type = media_type_map.get(image_path.suffix.lower(), "image/jpeg")
    data = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")
    return data, media_type


def _parse_response(raw_text: str) -> dict:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        cleaned = raw_text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)


async def _call_claude_async(
    image_path: Path,
    client: anthropic.AsyncAnthropic,
) -> dict:
    """Make async API call."""
    image_data, media_type = _load_image_as_base64(image_path)
    prompt = _load_prompt()

    message = await client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=config.MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
    )
    return _parse_response(message.content[0].text.strip())


async def extract_nutrients_async(
    image_path: Path,
    client: anthropic.AsyncAnthropic,
    semaphore: asyncio.Semaphore,
) -> ExtractionResult:
    """
    Extract nutrients from a single image with retry logic.
    Semaphore controls max concurrent API calls.
    """
    async with semaphore:
        last_error = None

        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                result = await _call_claude_async(image_path, client)

                has_data = result.get("has_data", False)

                if not has_data:
                    return ExtractionResult(
                        image_name=image_path.name,
                        has_data=False,
                        parse_status="no_data",
                        serving_size=None,
                        nutrients=[],
                    )

                raw_nutrients = [
                    RawNutrient(
                        name_raw=n.get("name_raw", ""),
                        amount=n.get("amount"),
                        unit=n.get("unit"),
                        daily_value_pct=n.get("daily_value_pct"),
                    )
                    for n in result.get("nutrients", [])
                    if n.get("name_raw")
                ]

                return ExtractionResult(
                    image_name=image_path.name,
                    has_data=True,
                    parse_status=result.get("parse_status", "complete"),
                    serving_size=result.get("serving_size"),
                    nutrients=raw_nutrients,
                )

            except json.JSONDecodeError as e:
                last_error = f"JSON parse error: {e}"
                logger.warning(
                    f"Attempt {attempt}/{config.MAX_RETRIES} failed for "
                    f"{image_path.name}: {last_error}"
                )

            except anthropic.APIError as e:
                last_error = f"API error: {e}"
                if "credit balance" in str(e).lower() or "billing" in str(e).lower():
                    logger.error(
                        f"Billing error for {image_path.name} — stopping retries"
                    )
                    break
                logger.warning(
                    f"Attempt {attempt}/{config.MAX_RETRIES} failed for "
                    f"{image_path.name}: {last_error}"
                )

            if attempt < config.MAX_RETRIES:
                await asyncio.sleep(config.RETRY_DELAY * attempt)

        logger.error(
            f"All {config.MAX_RETRIES} attempts failed for {image_path.name}"
        )
        return ExtractionResult(
            image_name=image_path.name,
            has_data=False,
            parse_status="failed",
            serving_size=None,
            nutrients=[],
            error=last_error,
        )