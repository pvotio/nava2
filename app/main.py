from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api import admin, auth, reports
from .core.config import settings
from .core.logging import configure_logging
from .core.openapi import apply_custom_openapi

configure_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    openapi_url=settings.OPENAPI_URL,
)

app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")
app.include_router(auth.router, prefix=settings.API_V1)
app.include_router(reports.router, prefix=settings.API_V1)
app.include_router(admin.router, prefix=settings.API_V1)

app.openapi = lambda: apply_custom_openapi(app)


@app.get("/")
def health():
    return {"status": "ok"}
