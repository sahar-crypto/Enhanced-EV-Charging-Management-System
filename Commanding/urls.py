from django.urls import path
from .views import SendCommandAPIView

urlpatterns = [
    path('station/<str:station_code>/', SendCommandAPIView.as_view(), name='send-command'),
]
