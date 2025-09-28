from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core.config import settings
from ..deps import get_db_dep, require_admin
from ..models import Report, ReportStatus, User
from ..services.templates_repo import registry

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


def _ok(**data: Any) -> dict[str, Any]:
    out = {"ok": True, "scope": "admin-only"}
    out.update(data)
    return out


@router.get("/health")
def admin_health():
    return _ok()


@router.get("/templates")
def list_templates():
    return _ok(templates=registry.list_templates())


@router.get("/templates/{template_id}")
def get_template(template_id: str):
    tmpl = registry.get_template(template_id)
    if not tmpl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return _ok(template=tmpl)


@router.post("/templates/sync")
def force_sync_templates(force: bool = False):
    registry.sync_index()
    n = registry.sync_all_assets(force=force)
    return _ok(synced=n, forced=bool(force))


@router.post("/templates/{template_id}/sync")
def sync_one_template(template_id: str, force: bool = False):
    """Fetch & cache assets for a single template."""
    tmpl = registry.get_template(template_id)
    if not tmpl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    registry.fetch_and_cache_assets(tmpl, force=force)
    data = registry.get_cached_assets(template_id)
    return _ok(
        template_id=template_id,
        cached=bool(data),
        forced=bool(force),
        has_html=bool(data and data.get("html")),
        has_logic=bool(data and data.get("logic")),
        has_test=bool(data and data.get("test")),
    )


@router.get("/templates/{template_id}/assets")
def get_cached_assets(template_id: str, include_bodies: bool = False):
    """Inspect cached assets. By default returns flags + meta only.

    Set include_bodies=true to return raw bodies (careful: large).
    """
    data = registry.get_cached_assets(template_id)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assets not cached")

    if include_bodies:
        return _ok(
            template_id=template_id,
            meta=data["meta"],
            html=data["html"],
            logic=data["logic"],
            test=data["test"],
        )

    return _ok(
        template_id=template_id,
        meta=data["meta"],
        has_html=bool(data["html"]),
        has_logic=bool(data["logic"]),
        has_test=bool(data["test"]),
    )


@router.get("/reports")
def admin_list_reports(
    db: Session = Depends(get_db_dep),
    status_filter: ReportStatus | None = Query(None, description="Filter by status: P/F/G/D"),
    email_like: str | None = Query(None, description="Filter by user email (ILIKE)"),
    template_id: str | None = Query(None, description="Filter by template_id"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    order: str = Query("created_at", pattern="^(created_at|updated_at)$"),
    desc: bool = Query(True),
):
    """Admin audit: list reports with optional filters.

    Returns a page with summary info (no HTML bodies).
    """
    q = db.query(Report, User.email).join(User, User.id == Report.user_id)

    if status_filter is not None:
        q = q.filter(Report.status == status_filter)
    if email_like:
        q = q.filter(User.email.ilike(f"%{email_like}%"))
    if template_id:
        q = q.filter(Report.template_id == template_id)

    total = q.count()

    col = Report.created_at if order == "created_at" else Report.updated_at
    if desc:
        q = q.order_by(col.desc())
    else:
        q = q.order_by(col.asc())

    rows: list[tuple[Report, str]] = q.offset(offset).limit(limit).all()

    items = []
    for r, email in rows:
        pdf_url = f"{settings.BASE_URL}/media/{r.output_file}" if r.output_file else None
        items.append(
            {
                "id": str(r.id),
                "hash_id": str(r.hash_id),
                "status": r.status.value,
                "template_id": r.template_id,
                "user_email": email,
                "pdf_url": pdf_url,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            }
        )

    return _ok(
        total=total,
        limit=limit,
        offset=offset,
        order=order,
        desc=desc,
        results=items,
    )


@router.get("/reports/{hash_id}")
def admin_get_report(
    hash_id: str,
    include_bodies: bool = Query(False, description="Include output_content (HTML)"),
    db: Session = Depends(get_db_dep),
):
    """Admin audit: fetch one report by hash_id.

    When include_bodies=true, returns the stored output_content (HTML) as well.
    """
    r = (
        db.query(Report, User.email)
        .join(User, User.id == Report.user_id)
        .filter(Report.hash_id == hash_id)
        .first()
    )
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    report, email = r
    pdf_url = f"{settings.BASE_URL}/media/{report.output_file}" if report.output_file else None

    payload = {
        "id": str(report.id),
        "hash_id": str(report.hash_id),
        "status": report.status.value,
        "template_id": report.template_id,
        "user_email": email,
        "pdf_url": pdf_url,
        "created_at": report.created_at,
        "updated_at": report.updated_at,
    }
    if include_bodies:
        payload["output_content"] = report.output_content or ""

    return _ok(report=payload)
