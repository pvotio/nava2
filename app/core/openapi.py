from fastapi.openapi.utils import get_openapi

from .config import settings


def apply_custom_openapi(app):
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description=(
            "API for async report generation.\n\n"
            "Use **/auth/login** to get a JWT, then click **Authorize** (top-right) "
            "and paste the token to call protected endpoints."
        ),
        routes=app.routes,
        servers=[{"url": settings.BASE_URL}],
        tags=[
            {"name": "auth", "description": "Authentication & token retrieval"},
            {"name": "reports", "description": "Create and track reports"},
            {"name": "admin", "description": "Admin-only operations"},
        ],
    )
    comps = schema.setdefault("components", {})
    schemes = comps.setdefault("securitySchemes", {})
    if "HTTPBearer" in schemes:
        default_scheme_name = "HTTPBearer"
    else:
        schemes["bearerAuth"] = {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
        default_scheme_name = "bearerAuth"

    schema["security"] = [{default_scheme_name: []}]
    app.openapi_schema = schema
    return app.openapi_schema
