from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        """
        Create and save a User with the given username and password.
        Adjusts is_staff and is_superuser based on the user type.
        """

        if username:
            if not password:
                raise ValueError('Users must have a password')

            user_type = extra_fields.get("type", "customer") # default to customer
            is_staff = extra_fields.get("is_staff", False)

            # Set is_staff and is_superuser based on the user type
            if user_type == "admin":
                extra_fields.setdefault("is_staff", True)
                extra_fields.setdefault("is_superuser", False)
            else:  # customer or organization
                extra_fields.setdefault("is_staff", False)
                extra_fields.setdefault("is_superuser", False)
            if is_staff:
                extra_fields.setdefault("type", "admin")
            user = self.model(username=username, **extra_fields)
            user.set_password(password)
            user.save(using=self._db)
            return user
        raise ValueError('Users must have a username')

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('type', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, password, **extra_fields)


    # No need to add this method as it is already in the BaseUserManager
    # and does the same functionality
    # def get_by_natural_key(self, username):
    #     return self.get(username=username)

class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('organization', 'Organization'),
        ('customer', 'Customer'),
    )
    username = models.CharField(unique=True, max_length=50, null=False)
    email = models.EmailField(unique=True, null=True)
    full_name = models.CharField(max_length=100, null=True)
    phone_number = models.CharField(max_length=11, null=True)
    type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, null=False)
    # last_login = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(null=True)

    USERNAME_FIELD = 'username'

    objects = CustomUserManager()

    def natural_key(self):
        return (self.username,)

class OrganizationManager(models.Manager):
    def get_by_natural_key(self, acronym):
        return self.get(acronym=acronym)

class Organization(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='organization_user')
    organization_name = models.CharField(max_length=100)
    acronym = models.CharField(max_length=10, null=False, unique=True)
    address = models.TextField(null=True)

    objects = OrganizationManager()

    def __str__(self):
        return f"{self.user.get_username()} @ {self.organization_name}"

    def natural_key(self):
        return (self.acronym,)

class CustomerManager(models.Manager):
    def get_by_natural_key(self, username):
        return self.get(user__username=username)

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_user')
    invoicing_address = models.TextField(null=True)
    car_plate = models.CharField(null=False, unique=True, max_length=8)

    objects = CustomerManager()
    def __str__(self):
        return f"Client: {self.user.get_username()} - Car: {self.car_plate}"

    def natural_key(self):
        return (self.user.username)

class PaymentMethod(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_payment_method')
    name = models.CharField(max_length=100)
    number = models.CharField(max_length=16, null=False)
    expiry_year = models.IntegerField(null=False)
    expiry_month = models.IntegerField(null=False)
    cvv = models.CharField(max_length=3, null=False)

    def __str__(self):
        return f"xxxx-xxxx-xxxx-{self.number[12:]}"