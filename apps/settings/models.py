from django.db import models

class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True)
    data_type = models.CharField(max_length=20, default='string')  # string, int, decimal, bool, json
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return f"{self.key} = {self.value}"

    @classmethod
    def get(cls, key, default=None):
        try:
            setting = cls.objects.get(key=key)
            if setting.data_type == 'int':
                return int(setting.value)
            elif setting.data_type == 'decimal':
                from decimal import Decimal
                return Decimal(setting.value)
            elif setting.data_type == 'bool':
                return setting.value.lower() in ('true', '1', 'yes')
            elif setting.data_type == 'json':
                import json
                return json.loads(setting.value)
            return setting.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, key, value, data_type='string', description=''):
        import json
        if data_type == 'json':
            value = json.dumps(value)
        elif data_type == 'bool':
            value = 'true' if value else 'false'
        else:
            value = str(value)
        obj, created = cls.objects.update_or_create(
            key=key,
            defaults={'value': value, 'data_type': data_type, 'description': description}
        )
        return obj