from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_dir: Path = Path("data")
    output_dir: Path = Path("output")

    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_prefix": "INGESTION_"}


settings = Settings()
