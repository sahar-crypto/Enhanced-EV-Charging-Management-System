from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from .serializers import UserSerializer, CustomerSerializer, OrganizationSerializer, PaymentMethodSerializer
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
)
from django.contrib.auth import authenticate
from .models import *
from Charging.models import *
from Commanding.models import *

class PermissionedModelViewSet(viewsets.ModelViewSet):
    """
    A reusable viewset that restricts access to the object owner or admin.
    """

    def has_object_permission(self, request, obj):
        return request.user == obj or request.user.is_staff
    def get_queryset(self):
        """
        Restrict listing to only the authenticated user or admins.
        """
        user = self.request.user

        if user.is_staff:  # Admins can see all users
            return super().get_queryset()

        # Normal users should only see their own record
        return super().get_queryset().filter(username=user.username)

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        if not self.has_object_permission(request, obj):
            raise PermissionDenied("You don't have permission to view this object.")
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        if not self.has_object_permission(request, obj):
            raise PermissionDenied("You can't update this object.")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if not self.has_object_permission(request, obj):
            raise PermissionDenied("You don't have permission to delete this object.")
        return super().destroy(request, *args, **kwargs)

class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            response = super().post(request, *args, **kwargs)

            # Include user information in the response
            return Response({
                'access': response.data['access'],
                'refresh': response.data['refresh'],
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'type': user.type,
                }
            }, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class UserViewSet(PermissionedModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'


class CustomerViewSet(PermissionedModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    lookup_field = 'user__username'

    # Commented this method because it does exactly what the create method
    # in the ModelViewSet does

    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #     headers = self.get_success_headers(serializer.data)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class OrganizationViewSet(PermissionedModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    lookup_field = 'acronym'

class PaymentMethodViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer

    # Commented this method because it is useless as we are setting the
    # permissions for each group of users based on their type.

    # def get_permissions(self):
    #     if self.action == 'list':
    #         return [IsAuthenticated(), IsCustomerOrAdmin()]
    #     elif self.action == 'retrieve':
    #         return [IsAuthenticated(), IsCustomerOrAdmin()]
    #     elif self.action == 'create':
    #         return [IsAuthenticated()]
    #     elif self.action in ['update', 'partial_update']:
    #         return [IsAuthenticated(), IsCustomerOrAdmin()]  # Only owner can update
    #     elif self.action == 'destroy':
    #         return [IsAuthenticated(), IsCustomerOrAdmin()]  # Only admin can delete
    #     return super().get_permissions()

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def retrieve_organization_customer(request, username):
    """
    API view to retrieve a customer that is related to an organization.
    """

    user = request.user

    if not hasattr(user, "organization_user"):
        return Response({"error": "Only organizations can access this endpoint."}, status=403)

    organization = user.organization_user
    stations = Station.objects.filter(organization=organization)
    chargers = EVCharger.objects.filter(station__in=stations)

    # Check if the customer has used any of the organization's chargers
    exists = Transaction.objects.filter(
        ev_charger__in=chargers,
        customer__user__username=username
    ).exists()

    if not exists:
        return Response({"error": "This customer is not related to your organization."}, status=403)

    try:
        customer = Customer.objects.get(user__username=username)
    except Customer.DoesNotExist:
        return Response({"error": "Customer not found."}, status=404)

    serializer = CustomerSerializer(customer)
    return Response(serializer.data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organization_customers_list(request):
    """
    API view to list all customers that are related to an organization.
    """
    user = request.user

    if not user.type == "organization":
        raise PermissionDenied("Only organizations can access this endpoint.")

    organization = Organization.objects.filter(user=user).first()

    # Get all stations owned by the organization
    stations = Station.objects.filter(organization=organization)

    # Get all chargers at those stations
    chargers = EVCharger.objects.filter(station__in=stations)

    # Get all unique customer IDs who transacted using those chargers
    customer_ids = Transaction.objects.filter(
        charger__in=chargers
    ).values_list("customer_id", flat=True).distinct()

    customers = Customer.objects.filter(id__in=customer_ids)

    if not customers.exists():
        return Response({"message": "You have no customers yet."}, status=200)

    serializer = CustomerSerializer(customers, many=True)
    return Response(serializer.data)