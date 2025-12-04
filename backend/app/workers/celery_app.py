from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("crypto_payment_saas")
celery_app.conf.broker_url = settings.celery_broker_url
celery_app.conf.result_backend = settings.celery_result_url
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    "poll-deposits": {
        "task": "app.workers.tasks.poll_deposits",
        "schedule": 60.0,
    },
    "retry-webhooks": {
        "task": "app.workers.tasks.retry_webhooks",
        "schedule": 120.0,
    },
}
