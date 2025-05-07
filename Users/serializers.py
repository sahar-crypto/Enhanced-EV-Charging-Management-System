from .models import User, Customer, Organization, PaymentMethod
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class OrganizationSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.filter(type='organization')
    )

    class Meta:
        model = Organization
        fields = ['user', 'acronym', 'organization_name', 'address']

class CustomerSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.filter(type='customer')
    )

    class Meta:
        model = Customer
        fields = ['user', 'car_plate', 'invoicing_address']

    # Commented this because it already exists in the parent class

    # def to_representation(self, instance):
    #     """ Customize output so user details are properly shown """
    #     representation = super().to_representation(instance)
    #     representation['user'] = UserSerializer(instance.user).data
    #     return representation

class PaymentMethodSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentMethod
        fields = '__all__'


