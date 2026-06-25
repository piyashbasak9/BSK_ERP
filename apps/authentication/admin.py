from django.contrib import admin
from .models import User, AllowedUrl

admin.site.register(User)
admin.site.register(AllowedUrl)
