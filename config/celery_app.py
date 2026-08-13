from celery import Celery
import os

celery_app = Celery(
    "worker",
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    include=["config.tasks"]
)

celery_app.conf.update(
    task_routes={
        "config.*":{"queue": "celery"}
    }
)