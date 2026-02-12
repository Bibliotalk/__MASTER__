import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .router import router


def _configure_logging() -> None:
    # Trafilatura can emit extremely verbose warnings (e.g. from `trafilatura.xml`).
    # Keep ingestion logs usable by default.
    for logger_name in ("trafilatura", "trafilatura.xml"):
        logging.getLogger(logger_name).setLevel(logging.ERROR)


_configure_logging()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Bibliotalk Ingestion Worker", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1/ingestion")


def cli() -> None:
    uvicorn.run(
        "ingestion.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    cli()
