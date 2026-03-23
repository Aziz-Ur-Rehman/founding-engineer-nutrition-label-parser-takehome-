import argparse
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract structured nutrition data from product label images."
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=os.getenv("INPUT_DIR", "Sample_images"),
        help="Folder containing product label images",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.getenv("OUTPUT_DIR", "output"),
        help="Folder to write output CSV",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=os.getenv("OUTPUT_FILE", "nutrition_data.csv"),
        help="Output CSV filename",
    )
    return parser.parse_args()


def main():
    from source_code.pipeline import run_pipeline

    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_file = output_dir / args.output_file

    run_pipeline(input_dir, output_file)


if __name__ == "__main__":
    main()
