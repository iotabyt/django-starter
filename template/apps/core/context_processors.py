from django.conf import settings
from django.http import HttpRequest


def project(request: HttpRequest) -> dict[str, str]:
    return {"PROJECT_NAME": settings.PROJECT_NAME}
