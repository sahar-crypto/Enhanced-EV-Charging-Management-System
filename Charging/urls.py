from django.urls import path
from .views import (
    list_stations,
    retrieve_station,
    update_station,
    delete_station,
    create_station,
    list_evchargers,
    retrieve_evcharger,
    update_evcharger,
    delete_evcharger,
    create_evcharger,
    )

app_name = 'charging'

urlpatterns = [
    path('stations/', list_stations, name='station-list'),
    path('station/new/', create_station, name='station-new'),
    path('station/<str:station_code>/', retrieve_station, name='station-retrieve'),
    path('station/<str:station_code>/update/', update_station, name='station-update'),
    path('station/<str:station_code>/delete/', delete_station, name='station-delete'),
    path('evchargers/', list_evchargers, name='evchargers'),
    path('evcharger/new/', create_evcharger, name='evcharger-new'),
    path('evcharger/<str:serial_number>/', retrieve_evcharger, name='evcharger-retrieve'),
    path('evcharger/<str:serial_number>/update/', update_evcharger, name='evcharger-update'),
    path('evcharger/<str:serial_number>/delete/', delete_evcharger, name='evcharger-delete'),
]
