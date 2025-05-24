from django.contrib import admin

from .models import Transaction, StatusLog, HeartbeatLog

admin.site.register(Transaction)
admin.site.register(StatusLog)
admin.site.register(HeartbeatLog)