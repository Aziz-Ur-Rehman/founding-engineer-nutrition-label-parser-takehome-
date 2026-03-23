import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    # API
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-opus-4-5")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", 1000))

    # Paths
    INPUT_DIR: Path = Path(os.getenv("INPUT_DIR", "Sample_images"))
    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "output"))
    OUTPUT_FILE: str = os.getenv("OUTPUT_FILE", "nutrition_data.csv")
    PROMPT_PATH: Path = Path("prompts/extraction_prompt.txt")
    LOG_DIR: Path = Path(os.getenv("LOG_DIR", "logs"))

    # Pipeline
    SUPPORTED_EXTENSIONS: frozenset = frozenset({".jpg", ".jpeg", ".png", ".webp"})
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", 3))
    RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", 2.0))
    MAX_CONCURRENCY: int = int(os.getenv("MAX_CONCURRENCY", 5))

    @classmethod
    def validate(cls) -> None:
        """Fail fast if required config is missing."""
        if not cls.ANTHROPIC_API_KEY:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. "
                "Add it to your .env file."
            )
        if not cls.INPUT_DIR.exists():
            raise FileNotFoundError(
                f"Input directory '{cls.INPUT_DIR}' does not exist."
            )
        if not cls.PROMPT_PATH.exists():
            raise FileNotFoundError(
                f"Prompt file '{cls.PROMPT_PATH}' does not exist."
            )


config = Config()