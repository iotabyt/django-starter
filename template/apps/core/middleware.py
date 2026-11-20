import logging
from collections.abc import Callable

from django.db import connection
from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class HealthCheckMiddleware:
    """Answer `GET /up` before anything else runs.

    kamal-proxy polls /up over plain HTTP with the container IP as the Host header, so this
    must run before ALLOWED_HOSTS validation (never call request.get_host() here) and before
    SecurityMiddleware's HTTPS redirect. It checks the database too, so a release that can't
    reach Postgres never goes live.
    """

    path = "/up"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path_info == self.path and request.method in ("GET", "HEAD"):
            return self.check()
        return self.get_response(request)

    def check(self) -> HttpResponse:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            logger.exception("Health check failed: database unavailable")
            return HttpResponse("database unavailable", status=503, content_type="text/plain")
        return HttpResponse("ok", content_type="text/plain")
