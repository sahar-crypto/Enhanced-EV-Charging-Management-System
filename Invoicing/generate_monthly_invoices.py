from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import datetime
from .models import Invoice  # Adjust import to your app
from django.db import transaction as db_transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate invoices for all users for the current month'

    def handle(self, *args, **kwargs):
        now = datetime.now()
        month = now.month
        year = now.year

        users = User.objects.all()

        for user in users:
            # Optional: Check if invoice already exists for this user this month
            if Invoice.objects.filter(user=user, month=month, year=year).exists():
                self.stdout.write(self.style.WARNING(f"Invoice already exists for {user.username}"))
                continue

            with db_transaction.atomic():
                invoice = Invoice.objects.create(
                    user=user,
                    month=month,
                    year=year
                )
                self.stdout.write(self.style.SUCCESS(f"Invoice created for {user.username}: Total Amount {invoice.total_amount}"))
