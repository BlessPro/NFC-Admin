from django.core.management.base import BaseCommand

from cards.models import Customer
from cards.services import create_customer_user


class Command(BaseCommand):
    help = "Create portal accounts for customers without users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--send-email",
            action="store_true",
            help="Send welcome emails to customers",
        )

    def handle(self, *args, **options):
        send_email = options.get("send_email", False)
        count = 0
        for customer in Customer.objects.filter(user__isnull=True):
            create_customer_user(customer, send_email=send_email)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Created {count} client user(s)."))
