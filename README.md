# Nutrition Label Parser

Takes a folder of product label images and produces a structured CSV of nutritional information.

---

## How It Works

```
Image → Classify + Extract (Claude Vision) → Normalize → CSV
```

Each image goes through a single Claude API call that first checks whether the image actually has a nutrition table, then extracts the data if it does. Normalization is plain Python — no LLM involved. All images are processed concurrently so the pipeline doesn't slow down as you add more.

### Structure

```
├── main.py
├── prompts/
│   └── extraction_prompt.txt
└── source_code/
    ├── config.py
    ├── models.py
    ├── extractor.py
    ├── normalizer.py
    ├── pipeline.py
    ├── writer.py
    └── data/
        ├── nutrient_map.py
        └── unit_map.py
```

---

## The Decisions

**Why one API call instead of two.**
The obvious approach is two calls — one to check if the image has nutrition data, one to extract it. I combined them into one. The prompt asks Claude to make the classification decision first, and the response schema enforces it: if `has_data` is false, the nutrients are ignored no matter what the model returned. Same result, half the cost.

**Why async.**
Sequential processing is fine at 13 images. At a few hundred it becomes the bottleneck. I use `asyncio` with a semaphore to run images concurrently while staying within API rate limits. The concurrency limit is configurable — you don't need to touch the code to tune it.

**Why snake_case for unknown nutrients.**
Not every nutrient on a label will be in my mapping table. Rather than returning null for the standard name — which is awkward to work with downstream — I convert the raw name to snake_case and use that. The original name is always preserved so nothing is lost.

**Why I kept original_amount and original_unit.**
For some nutrients I convert units — Vitamin D from µg to IU, for example. But I always store what the label actually said alongside the converted value. If a conversion is wrong, you can see it and fix it. Without the originals, a bad conversion is invisible.

**Why I didn't convert IU to mg.**
The conversion factor between IU and mg depends on the specific nutrient, and for some nutrients it depends on the form too. Getting it wrong silently is worse than leaving it for a downstream step that knows the context. I only convert where it's unambiguous.

---

## Output

| Column | Description |
|---|---|
| `product_image` | Source filename |
| `serving_size` | As printed on the label |
| `parse_status` | `complete`, `partial`, `no_data`, or `failed` |
| `nutrient_name_raw` | Exactly as it appeared on the label |
| `nutrient_name_standard` | Normalised e.g. `vitamin_c` |
| `amount` | Numeric value |
| `unit` | Normalised unit |
| `original_amount` | What the label said |
| `original_unit` | What the label said |
| `daily_value_pct` | % daily value if present |

---

## What I'd Do Next

The biggest gap right now is no ground truth to measure against. Before using this in production, I'd manually label a handful of images and compute precision and recall per field. After that — caching API responses so re-runs don't re-call Claude, and growing the nutrient map based on what falls through to the snake_case fallback.

---

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Add your ANTHROPIC_API_KEY

python main.py

# Or override the defaults
python main.py --input-dir my_images --output-dir results
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required |
| `CLAUDE_MODEL` | `claude-opus-4-5` | Model to use |
| `MAX_TOKENS` | `1000` | Max tokens per response |
| `INPUT_DIR` | `Sample_images` | Input folder |
| `OUTPUT_DIR` | `output` | Output folder |
| `OUTPUT_FILE` | `nutrition_data.csv` | Output filename |
| `MAX_RETRIES` | `3` | Retry limit per image |
| `RETRY_DELAY` | `2.0` | Base delay between retries (seconds) |
| `MAX_CONCURRENCY` | `5` | Max simultaneous API calls |