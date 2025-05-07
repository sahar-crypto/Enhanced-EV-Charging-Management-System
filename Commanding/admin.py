from django.contrib import admin

from .models import Transaction, StatusLog

admin.site.register(Transaction)
admin.site.register(StatusLog)