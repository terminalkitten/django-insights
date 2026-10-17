from django.contrib.auth import get_user_model, login


class DevAutoLogin:
    """Demo only: auto-login a dev user"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            user, _ = get_user_model().objects.get_or_create(email='dev@example.com')
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return self.get_response(request)
