from django.db import models
from Users.models import *

class StationManager(models.Manager):
    def get_by_natural_key(self, station_code):
        return self.get(station_code=station_code)

class Station(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='organization')
    station_code = models.CharField(max_length=100, unique=True, null=False)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)

    objects = StationManager()

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.station_code,)

class EVChargerManager(models.Manager):
    def get_by_natural_key(self, serial_number):
        return self.get(serial_number=serial_number)

class EVCharger(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('busy', 'Busy'),
    ]
    ACTIVITY_CHOICES = [
        ('charging', 'Charging'),
        ('idle', 'Idle'),
    ]
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='station')
    serial_number = models.CharField(max_length=100, unique=True, null=False)
    model = models.CharField(max_length=100, null=True)
    vendor = models.CharField(max_length=100, null=True)
    capacity = models.IntegerField(null=True)
    status = models.CharField(default='available', max_length=10, choices=STATUS_CHOICES)
    connected = models.BooleanField(default=False)
    activity = models.CharField(default='idle', max_length=10, choices=ACTIVITY_CHOICES)

    objects = EVChargerManager()

    def __str__(self):
        return self.serial_number

    def natural_key(self):
        return (self.serial_number,)