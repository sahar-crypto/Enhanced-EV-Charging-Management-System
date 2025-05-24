from django.db import models
from Users.models import *
from Charging.models import *

class Transaction(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_transaction')
    command = models.CharField(max_length=10)
    amount = models.FloatField(null=True)
    date = models.DateTimeField(auto_now_add=True)
    charger = models.ForeignKey(EVCharger, on_delete=models.CASCADE)

    def __str__(self):
        return f"Customer: {self.customer.user.username} consumed {self.amount} on charger {self.charger.serial_number}"

class StatusLog(models.Model):
    charger = models.ForeignKey(EVCharger, on_delete=models.CASCADE, related_name='charger')
    status = models.CharField(max_length=10)
    payload = models.JSONField(null=True)
    date = models.DateTimeField(auto_now_add=True)

class HeartbeatLog(models.Model):
    charger = models.ForeignKey(EVCharger, on_delete=models.CASCADE, related_name='heartbeats')
    received_at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField(null=True)

    def __str__(self):
        return f"Heartbeat from {self.charger.serial_number} at {self.received_at}"