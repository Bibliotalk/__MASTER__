import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_dir: Path = Path("data")
    output_dir: Path = Path("output")

    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    worker_secret: str = ""
    api_base_url: str = "http://localhost:4000"

    crawler_max_pages: int = 5000

    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_prefix": "INGESTION_"}


load_dotenv()
settings = Settings(
    openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
    openai_model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
)
