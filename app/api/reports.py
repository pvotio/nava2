from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.config import settings
from ..deps import get_current_user, get_db_dep
from ..models import Report, ReportStatus, Template
from ..schemas import ReportCreate, ReportOut
from ..tasks import generate_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportOut)
def create_report(
    payload: ReportCreate, db: Session = Depends(get_db_dep), user=Depends(get_current_user)
):
    template = db.query(Template).filter(Template.id == payload.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    r = Report(user_id=user.id, template_id=template.id, input_args=payload.input_args)
    db.add(r)
    db.commit()
    db.refresh(r)

    # enqueue task
    generate_report.delay(str(r.id))

    return ReportOut(hash_id=r.hash_id, status=r.status.value)


@router.get("/{hash_id}", response_model=ReportOut)
def get_report(hash_id: UUID, db: Session = Depends(get_db_dep), user=Depends(get_current_user)):
    r = db.query(Report).filter(Report.hash_id == hash_id, Report.user_id == user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    pdf_url = None
    if r.status == ReportStatus.GENERATED and r.output_file:
        pdf_url = f"{settings.BASE_URL}/media/{r.output_file}"
    return ReportOut(
        hash_id=r.hash_id,
        status=r.status.value,
        pdf_url=pdf_url,
        output_content=r.output_content or None,
    )
