from django.contrib import admin
from .models import Account, JournalEntry, JournalItem

admin.site.register((Account, JournalEntry, JournalItem))
