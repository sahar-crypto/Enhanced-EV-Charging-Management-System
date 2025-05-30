from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/charging/station/(?P<station_code>[-\w]+)/(?P<serial_number>[-\w]+)/?$', consumers.ChargingConsumer.as_asgi()),
]
