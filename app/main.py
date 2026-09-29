from pathlib import Path

from fastapi import FastAPI

from fastapi.staticfiles import StaticFiles

from .config import settings

from .database import init_db

from .routes import router


BASE_DIR = Path(
    __file__
).resolve().parent.parent


app = FastAPI(

    title=settings.app_name,

    description=(
        "AI-powered 7-day fitness "
        "plan generator using Gemini."
    ),

    version="1.0.0",
)


app.mount(
    "/static",
    StaticFiles(
        directory=BASE_DIR / "static"
    ),
    name="static",
)


app.include_router(router)


@app.on_event("startup")
def startup():

    init_db()