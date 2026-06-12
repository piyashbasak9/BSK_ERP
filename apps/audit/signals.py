from django.db.models.signals import post_save, pre_delete, m2m_changed
from django.dispatch import receiver
from .models import AuditLog
from django.contrib.auth import get_user_model
import json

User = get_user_model()


def get_changed_fields(instance, old_instance):
    """Returns dict of changed fields with old and new values"""
    changes = {}
    for field in instance._meta.fields:
        field_name = field.name
        old_val = getattr(old_instance, field_name, None)
        new_val = getattr(instance, field_name, None)
        if old_val != new_val:
            changes[field_name] = {'old': str(old_val), 'new': str(new_val)}
    return changes


@receiver(post_save, weak=False)
def log_model_save(sender, instance, created, **kwargs):
    if sender.__name__ == 'AuditLog':
        return  # avoid recursion
    from django.contrib.sessions.models import Session
    if sender == Session:
        return

    request = get_current_request()  # we need to pass request context – see note
    user = getattr(request, 'user', None) if request else None
    if not user or not user.is_authenticated:
        return

    action = 'create' if created else 'update'
    old_vals = {}
    if not created:
        # To get old values, we need to fetch the previous instance.
        # We store old values in a thread-local variable before save.
        # For simplicity, we'll skip old_values for now, but in production use a proper approach.
        pass

    AuditLog.objects.create(
        user=user,
        username=user.username,
        action=action,
        resource=sender.__name__,
        resource_id=str(instance.pk) if instance.pk else '',
        old_values=old_vals,
        new_values={field: str(getattr(instance, field)) for field in instance._meta.fields if not field.primary_key},
        ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR', '') if request else '',
        user_agent=getattr(request, 'META', {}).get('HTTP_USER_AGENT', '') if request else '',
    )


@receiver(pre_delete, weak=False)
def log_model_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = getattr(request, 'user', None) if request else None
    if not user or not user.is_authenticated:
        return
    AuditLog.objects.create(
        user=user,
        username=user.username,
        action='delete',
        resource=sender.__name__,
        resource_id=str(instance.pk) if instance.pk else '',
        old_values={field: str(getattr(instance, field)) for field in instance._meta.fields if not field.primary_key},
        new_values={},
        ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR', '') if request else '',
        user_agent=getattr(request, 'META', {}).get('HTTP_USER_AGENT', '') if request else '',
    )


# Helper to get current request from thread local
from threading import local
_request_local = local()

def get_current_request():
    return getattr(_request_local, 'request', None)

class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        _request_local.request = request
        response = self.get_response(request)
        return response