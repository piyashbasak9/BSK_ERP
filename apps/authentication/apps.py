from django.apps import AppConfig
from django.urls import get_resolver
from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.authentication'
    verbose_name = 'Authentication'

    def ready(self):
        if not settings.DEBUG and getattr(settings, 'RUN_MAIN', True) is False:
            return
        self.sync_allowed_urls()

    def sync_allowed_urls(self):
        from apps.authentication.models import AllowedUrl

        try:
            resolver = get_resolver()
            named_urls = self._collect_named_urls(resolver.url_patterns)
        except (OperationalError, ProgrammingError, ImportError):
            return

        for url_name, pattern in named_urls:
            if not url_name or url_name.startswith('admin:'):
                continue
            human_name = url_name.replace('_', ' ').replace('-', ' ').title()
            defaults = {'name': human_name, 'path': str(pattern)}
            allowed_url, created = AllowedUrl.objects.get_or_create(url_name=url_name, defaults=defaults)
            if not created and (allowed_url.path != defaults['path'] or allowed_url.name != defaults['name']):
                allowed_url.name = defaults['name']
                allowed_url.path = defaults['path']
                allowed_url.save(update_fields=['name', 'path'])
        # Refresh middleware cache of allowed url names (if middleware module is loaded)
        try:
            from erp.utils import middleware
            middleware._ALLOWED_URL_NAMES = set(AllowedUrl.objects.values_list('url_name', flat=True))
        except Exception:
            pass

    def _collect_named_urls(self, patterns):
        result = []
        for pattern in patterns:
            if hasattr(pattern, 'url_patterns'):
                result.extend(self._collect_named_urls(pattern.url_patterns))
            elif getattr(pattern, 'name', None):
                result.append((pattern.name, str(pattern.pattern)))
        return result
