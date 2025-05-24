from django.urls import path
from .views import StartSimulatorView

urlpatterns = [
    path('start/', StartSimulatorView.as_view(), name='start-simulator'),
]