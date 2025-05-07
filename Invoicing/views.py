from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from .models import Invoice
from .serializers import InvoiceSerializer
from django.shortcuts import get_object_or_404

# List all invoices
class InvoiceListView(generics.ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        # Instead of filtering by user, list all invoices (no filter)
        return Invoice.objects.all()

# Retrieve a single invoice by id
class InvoiceDetailView(generics.RetrieveAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter by invoice ID passed in URL
        return Invoice.objects.all()

    def get_object(self):
        # Fetch the invoice using the id in the URL
        return get_object_or_404(Invoice, pk=self.kwargs['pk'])

# Update an invoice (edit month, year, etc.)
class InvoiceUpdateView(generics.UpdateAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_object(self):
        # Fetch the invoice using the id in the URL
        return get_object_or_404(Invoice, pk=self.kwargs['pk'])

# Delete an invoice
class InvoiceDeleteView(generics.DestroyAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_object(self):
        # Fetch the invoice using the id in the URL
        return get_object_or_404(Invoice, pk=self.kwargs['pk'])

class InvoicePayView(APIView):
    permission_classes = [IsAuthenticated()]

    def post(self, request, pk):
        try:
            invoice = get_object_or_404(Invoice, pk=pk)
            # For now, just mark it as paid (add a 'is_paid' field if you want)
            invoice.status = 'Paid'
            invoice.save()
            return Response({'message': 'Invoice paid successfully.'})
        except Invoice.DoesNotExist:
            return Response({'error': 'Invoice not found.'}, status=status.HTTP_404_NOT_FOUND)
