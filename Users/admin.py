from django.contrib import admin

from .models import User, Customer, Organization, PaymentMethod

admin.site.register(User)
admin.site.register(Customer)
admin.site.register(Organization)
admin.site.register(PaymentMethod)
