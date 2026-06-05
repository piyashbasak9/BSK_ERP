from django.contrib import admin
from .models import DailyCollectionSheet, CollectionEntry

admin.site.register((DailyCollectionSheet, CollectionEntry))
