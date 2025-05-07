from django.contrib import admin

from .models import Station, EVCharger

admin.site.register(Station)
admin.site.register(EVCharger)