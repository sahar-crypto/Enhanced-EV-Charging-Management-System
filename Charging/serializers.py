from .models import Station, EVCharger
from Users.models import Organization
from rest_framework import serializers

class StationSerializer(serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(
        slug_field='acronym', queryset=Organization.objects.all()
    )
    class Meta:
        model = Station
        fields = ['organization', 'name', 'station_code', 'location']

class EVChargerSerializer(serializers.ModelSerializer):
    station = serializers.SlugRelatedField(
        slug_field='station_code', queryset=Station.objects.all()
    )
    class Meta:
        model = EVCharger
        fields = ['station', 'model', 'serial_number', 'vendor', 'capacity']
