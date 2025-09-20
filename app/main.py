from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api import auth, reports
from .core.config import settings
from .core.logging import configure_logging
from .db.postgres import Base, engine

configure_logging()

app = FastAPI(title=settings.PROJECT_NAME)
Base.metadata.create_all(bind=engine)
app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")
app.include_router(auth.router, prefix=settings.API_V1)
app.include_router(reports.router, prefix=settings.API_V1)


@app.get("/")
def health():
    return {"status": "ok"}
