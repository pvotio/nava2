from celery import Celery

from .core.config import settings
from .core.logging import configure_logging

configure_logging()

celery_app = Celery(
    "reports",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"],
)


celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    worker_hijack_root_logger=False,
)


celery_app.conf.beat_schedule.update(
    {
        "sync-templates-index": {
            "task": "app.tasks.sync_templates_index",
            "schedule": 60 * settings.TEMPLATES_SYNC_INTERVAL_MINUTES,
        },
        "sync-templates-assets": {
            "task": "app.tasks.sync_templates_assets",
            "schedule": 60 * settings.TEMPLATES_SYNC_INTERVAL_MINUTES,
        },
    }
)
