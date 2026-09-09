from app.core.config import settings

try:
    from celery import Celery
    
    broker_url = settings.REDIS_URL or "redis://localhost:6379/1"
    
    celery_app = Celery(
        "mospi_worker",
        broker=broker_url,
        backend=broker_url
    )
    
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
    )
except ImportError:
    # No silent fallback! Fail explicitly if called.
    class MissingCeleryTask:
        def delay(self, *args, **kwargs):
            raise RuntimeError("Celery is not installed or configured. Background tasks cannot be queued.")
            
    class MissingCelery:
        def task(self, *args, **kwargs):
            def decorator(func):
                func.delay = MissingCeleryTask().delay
                return func
            return decorator
            
    celery_app = MissingCelery()
