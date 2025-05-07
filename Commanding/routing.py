from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/charging/(?P<charger_id>\w+)/', consumers.ChargingStationConsumer.as_asgi()),
]
