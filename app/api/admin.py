from fastapi import APIRouter, Depends

from ..deps import require_admin

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


@router.get("/health")
def admin_health():
    return {"ok": True, "scope": "admin-only"}
