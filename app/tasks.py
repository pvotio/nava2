import json
import logging
from datetime import UTC, datetime

from .celery_app import celery_app
from .db.postgres import SessionLocal
from .models import Report, ReportStatus
from .services import aggregator
from .services.templates_repo import registry
from .services.validator import ValidationError, Validator

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.validate_report")
def validate_report(self, template_id: str, args: dict, report_id: str):
    logger.debug(
        "[task=%s] validate_report report_id=%s template_id=%s",
        self.request.id,
        report_id,
        template_id,
    )
    try:
        _, process_args = Validator(template_id, args).validate()
    except ValidationError as err:
        raise err
    return {
        "template_id": template_id,
        "report_id": report_id,
        "process_args": process_args,
    }


@celery_app.task(bind=True, name="app.tasks.fetch_placeholders")
def fetch_placeholders(self, data: dict):
    logger.debug(
        "[task=%s] fetch_placeholders report_id=%s", self.request.id, data.get("report_id")
    )
    placeholders = aggregator.fetch_placeholders(data["template_id"], data["process_args"])
    data["placeholders"] = placeholders
    return data


@celery_app.task(bind=True, name="app.tasks.generate_html")
def generate_html(self, data: dict):
    logger.debug("[task=%s] generate_html report_id=%s", self.request.id, data.get("report_id"))
    html, kwargs = aggregator.render_html(data["template_id"], data["placeholders"])
    data["html"] = html
    data["pdf_kwargs"] = kwargs
    return data


@celery_app.task(bind=True, name="app.tasks.generate_pdf")
def generate_pdf(self, data: dict):
    logger.debug("[task=%s] generate_pdf report_id=%s", self.request.id, data.get("report_id"))
    report_id = data["report_id"]
    db = SessionLocal()
    try:
        r: Report | None = db.query(Report).filter(Report.id == report_id).first()
        if not r:
            raise RuntimeError(f"Report not found: {report_id}")
        filename = f"report_{r.template_id}_{r.hash_id[:8]}.pdf"
        aggregator.render_pdf(filename, data["html"], data["pdf_kwargs"])
        r.output_file = filename
        r.updated_at = datetime.now(UTC)
        db.add(r)
        db.commit()
        return data
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.update_report_status")
def update_report_status(self, data: dict):
    logger.debug(
        "[task=%s] update_report_status report_id=%s", self.request.id, data.get("report_id")
    )
    report_id = data["report_id"]
    db = SessionLocal()
    try:
        r: Report | None = db.query(Report).filter(Report.id == report_id).first()
        if not r:
            return
        r.status = ReportStatus.GENERATED
        r.output_content = data.get("html", "")
        r.updated_at = datetime.now(UTC)
        db.add(r)
        db.commit()
        logger.info("Report %s marked GENERATED", report_id)
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.handle_errors")
def handle_errors(
    self, request=None, exc=None, traceback=None, stage=None, report_id=None, **kwargs
):
    logger.error("Error in %s for report %s: %s", stage, report_id, exc)
    message = "Unexpected error during report generation. Contact admin."
    error_body = {
        "verbose_message": f"{stage} - {exc} - {traceback}",
        "message": message,
    }

    from datetime import UTC, datetime

    from .db.postgres import SessionLocal
    from .models import Report, ReportStatus

    db = SessionLocal()
    try:
        r = db.query(Report).filter(Report.id == report_id).first()
        if r:
            r.status = ReportStatus.FAILED
            r.output_content = json.dumps(error_body)
            r.updated_at = datetime.now(UTC)
            db.add(r)
            db.commit()
    finally:
        db.close()


def generate_report_async(template_id: str, args: dict, report_id: str):
    sig = (
        validate_report.s(template_id, args, report_id).set(
            link_error=handle_errors.s(stage="validate_report", report_id=report_id)
        )
        | fetch_placeholders.s().set(
            link_error=handle_errors.s(stage="fetch_placeholders", report_id=report_id)
        )
        | generate_html.s().set(
            link_error=handle_errors.s(stage="generate_html", report_id=report_id)
        )
        | generate_pdf.s().set(
            link_error=handle_errors.s(stage="generate_pdf", report_id=report_id)
        )
        | update_report_status.s().set(
            link_error=handle_errors.s(stage="update_report_status", report_id=report_id)
        )
    )
    res = sig.apply_async()
    logger.info("Enqueued report pipeline report_id=%s celery_root_task_id=%s", report_id, res.id)
    return res


@celery_app.task(name="app.tasks.sync_templates_index")
def sync_templates_index():
    try:
        registry.sync_index()
    except Exception as e:
        logger.error("Failed syncing templates index: %s", e)


@celery_app.task(name="app.tasks.sync_templates_assets")
def sync_templates_assets(force: bool = False):
    try:
        n = registry.sync_all_assets(force=force)
        logger.info("Synced assets for %s templates", n)
    except Exception as e:
        logger.error("Failed syncing templates assets: %s", e)
