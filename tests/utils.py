SEED_AUTHORS = 20
SEED_BOOKS = 60


class AllowAll:
    def has_permission(self, request):
        return True


class DenyAll:
    def has_permission(self, request):
        return False
