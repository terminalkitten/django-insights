from collections.abc import Callable

from django.contrib.auth import get_user_model, login
from django.http import HttpRequest, HttpResponse


class DevAutoLogin:
    """Demo only: auto-login a dev user"""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not request.user.is_authenticated:
            user, _ = get_user_model().objects.get_or_create(email='dev@example.com')
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return self.get_response(request)
