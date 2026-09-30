from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import Base, engine
from .routes import router


BASE_DIR = Path(
    __file__
).resolve().parent.parent


Path(
    BASE_DIR / "data"
).mkdir(
    exist_ok=True
)


Base.metadata.create_all(
    bind=engine
)


settings = get_settings()


app = FastAPI(

    title=settings.app_name,

    version="1.0.0",

    description=(
        "FitBuddy AI Fitness Plan Generator "
        "using Google Gemini."
    ),
)


app.mount(

    "/static",

    StaticFiles(
        directory=str(
            BASE_DIR / "static"
        )
    ),

    name="static",
)


app.include_router(
    router
)


@app.get(
    "/favicon.ico",
    include_in_schema=False
)
def favicon():

    return ""