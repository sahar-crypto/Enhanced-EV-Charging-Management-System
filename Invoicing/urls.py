from django.urls import path
from .views import (
            InvoiceListView,
            InvoiceDetailView,
            InvoiceUpdateView,
            InvoiceDeleteView,
            InvoicePayView
            )

app_name = 'invoices'

urlpatterns = [
    path('all/', InvoiceListView.as_view(), name='invoices-all'),
    path('<int:pk>/', InvoiceDetailView.as_view(), name='invoice-detail'),
    path('<int:pk>/update/', InvoiceUpdateView.as_view(), name='invoice-update'),
    path('<int:pk>/delete/', InvoiceDeleteView.as_view(), name='invoice-delete'),
    path('<int:pk>/pay/', InvoicePayView.as_view(), name='invoice-pay'),
    ]