from django.contrib import admin
from .models import SavingsProduct, SavingsAccount, SavingsTransaction

admin.site.register((SavingsProduct, SavingsAccount, SavingsTransaction))
