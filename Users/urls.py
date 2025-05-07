from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
            LoginView,
            UserViewSet,
            CustomerViewSet,
            OrganizationViewSet,
            PaymentMethodViewSet,
            retrieve_organization_customer,
            organization_customers_list,
            )
# Added default routers because they're easier to use and less complicated
# And also less code writing
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'organizations', OrganizationViewSet)
router.register(r'payments', PaymentMethodViewSet)
urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('organization/mycustomers/', organization_customers_list),
    path('organization/mycustomers/<str:username>', retrieve_organization_customer),
]
