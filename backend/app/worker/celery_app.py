from app.core.config import settings

# Fallback gracefully if celery is not installed yet
try:
    from celery import Celery
    
    broker_url = settings.REDIS_URL or "memory://"
    
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
    # Dummy mock for local test collection when celery isn't installed
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("Celery is not installed. Background tasks will be mocked.")
    
    class DummyTask:
        def delay(self, *args, **kwargs):
            class DummyAsyncResult:
                id = "dummy-task-id-no-celery"
            return DummyAsyncResult()
            
    class DummyCelery:
        def task(self, *args, **kwargs):
            def decorator(func):
                func.delay = DummyTask().delay
                return func
            return decorator
            
    celery_app = DummyCelery()
