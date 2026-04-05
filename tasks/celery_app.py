import os

from celery import Celery

# Create the Celery app
# "tasks" = the name of this app (can be anything)
# broker = where jobs are stored (Redis)
# backend = where results are stored (also Redis)
celery_app = Celery(
    "tasks",
    broker=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    include=["tasks.transaction_tasks"],
)

# Configuration
celery_app.conf.update(
  # How long to keep task results (in seconds)
  result_expires=3600,  # 1 hour

  # Serialization format
  task_serializer="json",
  result_serializer="json",
  accept_content=["json"],

  # Timezone
  timezone="Asia/Kolkata",
)