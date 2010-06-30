from django.conf import settings

IS_PUBLIC = getattr(settings, "IS_PUBLIC", False)
IS_PRIVATE = not IS_PUBLIC
