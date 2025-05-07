from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import routing

# router = DefaultRouter()
#
# router.register(r'event', EventViewSet, basename='event')
# router.register(r'command', CommandViewSet, basename='command')
# router.register(r'log', CommandLogViewSet, basename='commandlog')

app_name = 'commanding'

urlpatterns = [
    re_path(r'ws/charging/(?P<charger_id>\w+)/', include(routing.websocket_urlpatterns)),  # Include WebSocket routing
    path('send-command/<str:station_id>/', views.send_remote_command, name='send_command'),
]
