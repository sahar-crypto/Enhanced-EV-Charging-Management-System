from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Station, EVCharger
from .serializers import StationSerializer, EVChargerSerializer
from django.shortcuts import get_object_or_404

# List API View
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_stations(request):
    stations = Station.objects.all()
    serializer = StationSerializer(stations, many=True)
    return Response(serializer.data)

# Retrieve API View
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_station(request, station_code):
    station = get_object_or_404(Station, station_code=station_code)
    serializer = StationSerializer(station)

    return Response(serializer.data)

# Update API View
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_station(request, station_code):
    station = get_object_or_404(Station, station_code=station_code)
    if not request.user.has_perm('Charging.change_station') and request.user != station.organization.user:
        return Response({"detail": "You do not have permission to access this station."},
                        status=status.HTTP_403_FORBIDDEN)
    if request.method == 'PATCH':
        serializer = StationSerializer(station, data=request.data, partial=True)
    else:
        serializer = StationSerializer(station, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Delete API View
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_station(request, station_code):
    station = get_object_or_404(Station, station_code=station_code)
    if not request.user.has_perm('Charging.delete_station') and request.user != station.organization.user:
        return Response({"detail": "You do not have permission to access this station."},
                        status=status.HTTP_403_FORBIDDEN)
    station.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

# Create API View
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_station(request):
    serializer = StationSerializer(data=request.data)
    if not request.user.has_perm('Charging.add_station'):
        return Response({"detail": "You do not have permission to create a station."},
                        status=status.HTTP_403_FORBIDDEN)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# List API View
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_evchargers(request):
    evchargers = EVCharger.objects.all()
    serializer = EVChargerSerializer(evchargers, many=True)
    return Response(serializer.data)

# Retrieve API View
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_evcharger(request, serial_number):
    evcharger = get_object_or_404(EVCharger, serial_number=serial_number)
    serializer = EVChargerSerializer(evcharger)
    return Response(serializer.data)

# Update API View
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_evcharger(request, serial_number):
    evcharger = get_object_or_404(EVCharger, serial_number=serial_number)
    if not request.user.has_perm('Charging.change_station') and request.user != evcharger.station.organization.user:
        return Response({"detail": "You do not have permission to access this station."},
                        status=status.HTTP_403_FORBIDDEN)
    if request.method == 'PATCH':
        serializer = EVChargerSerializer(evcharger, data=request.data, partial=True)
    else:
        serializer = EVChargerSerializer(evcharger, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Delete API View
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_evcharger(request, serial_number):
    evcharger = get_object_or_404(EVCharger, serial_number=serial_number)
    if not request.user.has_perm('Charging.delete_station') and request.user != evcharger.station.organization.user:
        return Response({"detail": "You do not have permission to access this station."},
                        status=status.HTTP_403_FORBIDDEN)
    evcharger.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

# Create API View
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_evcharger(request):
    serializer = EVChargerSerializer(data=request.data)
    if not request.user.has_perm('Charging.add_evcharger'):
        return Response({"detail": "You do not have permission to create an EV Charger."},
                        status=status.HTTP_403_FORBIDDEN)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
