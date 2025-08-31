from celery import Celery
from celery.schedules import crontab
from datetime import datetime
import subprocess
import os

from config import (
    DB_USER,
    DB_PASS,
    DB_HOST,
    DB_NAME,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_PASSWORD,
)

celery_app = Celery(
    "spendings_control",
    broker=f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0",
    backend=f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0",
)

celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    "daily-database-backup": {
        "task": "app.celery_app.backup_database",
        "schedule": crontab(hour=0, minute=0),
    }
}


@celery_app.task
def backup_database() -> str:
    """Dump the Postgres database into a timestamped SQL file."""
    timestamp = datetime.now().strftime("%Y-%m-%d")
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = os.path.join(backup_dir, f"backup_{timestamp}.sql")
    command = [
        "pg_dump",
        f"--dbname=postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}",
        "-f",
        backup_path,
    ]
    subprocess.run(command, check=True)
    return backup_path
