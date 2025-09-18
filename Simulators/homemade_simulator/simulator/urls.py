from django.urls import path
from .views import StartSimulatorView, StopSimulatorView

urlpatterns = [
    path('start/', StartSimulatorView.as_view(), name='start_simulator'),
    path('stop/', StopSimulatorView.as_view(), name='stop_simulator'),
]
