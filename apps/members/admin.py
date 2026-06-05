from django.contrib import admin
from .models import Member, Nominee, MemberTransfer

admin.site.register((Member, Nominee, MemberTransfer))
