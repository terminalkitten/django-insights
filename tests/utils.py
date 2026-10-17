SEED_USERS = 30
SEED_MESSAGES = 400


class AllowAll:
    def has_permission(self, request):
        return True


class DenyAll:
    def has_permission(self, request):
        return False


class NoMethod:
    pass
