import logging

from django.contrib.sessions.models import Session
from django.utils import timezone
from procrastinate.contrib.django import app

logger = logging.getLogger(__name__)


@app.task(queue="default")
def example_task(message: str) -> str:
    """Queue with `example_task.defer(message="hi")`; `bin/dev` runs a worker."""
    logger.info("example_task: %s", message)
    return message


@app.periodic(cron="0 2 * * *")
@app.task(queue="default", queueing_lock="nightly_cleanup")
def nightly_cleanup(timestamp: int) -> None:
    """Runs at 02:00 every night (server time zone) in the worker."""
    deleted, _ = Session.objects.filter(expire_date__lt=timezone.now()).delete()
    logger.info("nightly_cleanup: deleted %s expired sessions", deleted)
