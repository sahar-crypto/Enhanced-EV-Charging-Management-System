from django.db import models
from Users.models import PaymentMethod, User
from django.db.models import Sum
from decimal import Decimal


class Invoice(models.Model):
    INVOICE_STATUS = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    paid_amount = models.FloatField(default=0)
    due_amount = models.FloatField(default=0)
    status = models.CharField(max_length=100, default='Unpaid', choices=INVOICE_STATUS)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    date = models.DateField()

    @property
    def total_amount(self):
        """
        Aggregate all transaction amounts for this user and return the total.
        """
        total = self.user.user_transaction.filter(
            date__year=self.date.year,
            date__month=self.date.month
        ).aggregate(total=Sum('amount'))['total']
        return total or Decimal('0.00')

    def __str__(self):
        return f"Invoice for {self.user.username} - {self.date}"
