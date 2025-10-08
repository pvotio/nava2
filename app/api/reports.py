from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.config import settings
from ..deps import get_current_user, get_db_dep
from ..models import Report
from ..schemas import ReportCreate, ReportOut
from ..services.validator import ValidationError, Validator
from ..tasks import generate_report_async

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportOut)
def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db_dep),
    user=Depends(get_current_user),
):
    """Create a report request (auth required)."""
    try:
        _, process_args = Validator(payload.template_id, payload.input_args).validate()
    except ValidationError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err

    r = Report(user_id=user.id, template_id=payload.template_id, input_args=process_args)
    db.add(r)
    db.commit()
    db.refresh(r)

    generate_report_async(str(r.template_id), dict(r.input_args), str(r.id))
    return ReportOut(hash_id=r.hash_id, status=r.status.value)


@router.get("/{hash_id}", response_model=ReportOut)
def get_report(
    hash_id: UUID,
    db: Session = Depends(get_db_dep),
):
    """Public lookup by hash_id (no auth)."""
    r = db.query(Report).filter(Report.hash_id == hash_id).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    pdf_url = (
        f"{settings.BASE_URL.rstrip('/')}{settings.MEDIA_URL}/{r.output_file}"
        if r.output_file
        else None
    )
    return ReportOut(
        hash_id=r.hash_id,
        status=r.status.value,
        pdf_url=pdf_url,
    )
