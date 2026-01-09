from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from cards.constants import PACKAGES
from cards.models import Action, Customer, Order, Payment, Profile, Visit
from cards.services import create_customer_user, generate_unique_code, generate_unique_slug


class Command(BaseCommand):
    help = "Seed demo data for ThinkTech BizCards"

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin123")
            self.stdout.write(self.style.SUCCESS("Created admin user (admin/admin123)"))

        if Customer.objects.exists():
            self.stdout.write(self.style.WARNING("Customers already exist, skipping."))
            return

        demo_data = [
            {
                "full_name": "Akosua Mensah",
                "email": "akosua@example.com",
                "phone": "+233501112233",
                "package": "basic",
                "template_key": "business",
            },
            {
                "full_name": "Kojo Owusu",
                "email": "kojo@example.com",
                "phone": "+233501112244",
                "package": "pro",
                "template_key": "portfolio",
            },
            {
                "full_name": "Esi Badu",
                "email": "esi@example.com",
                "phone": "+233501112255",
                "package": "premium",
                "template_key": "restaurant",
            },
        ]

        for item in demo_data:
            customer = Customer.objects.create(
                full_name=item["full_name"],
                email=item["email"],
                phone=item["phone"],
                package=item["package"],
                status="active",
            )
            create_customer_user(customer, send_email=False)
            profile = Profile.objects.create(
                customer=customer,
                code=generate_unique_code(),
                slug=generate_unique_slug(item["full_name"]),
                template_key=item["template_key"],
                theme_json={
                    "mode": "light",
                    "primary": "#0d6efd",
                    "secondary": "#1f2937",
                    "accent": "#f59e0b",
                },
                content_json={
                    "full_name": item["full_name"],
                    "title": "Founder",
                    "company": "ThinkTech",
                    "phone": item["phone"],
                    "whatsapp": item["phone"],
                    "email": item["email"],
                    "website": "https://thinktechbizcards.com",
                    "bio": "Sample profile for demo.",
                    "links": [
                        {"label": "LinkedIn", "url": "https://linkedin.com"},
                    ],
                },
                status="live",
                hosting_expires_at=timezone.now() + timedelta(days=365),
            )
            order = Order.objects.create(
                customer=customer,
                profile=profile,
                package=item["package"],
                card_quantity=PACKAGES[item["package"]]["card_quantity"],
                shipping_name=item["full_name"],
                shipping_phone=item["phone"],
                shipping_address="Accra",
                status="paid",
                paid_at=timezone.now(),
            )
            Payment.objects.create(
                customer=customer,
                order=order,
                provider="manual",
                reference=f"demo-{profile.code}",
                amount=PACKAGES[item["package"]]["price"],
                currency="GHS",
                status="success",
                paid_at=timezone.now(),
                raw_payload={},
            )
            visit = Visit.objects.create(
                profile=profile,
                visited_at=timezone.now(),
                ip_hash="demo",
                user_agent="seed",
                device_type="desktop",
            )
            Action.objects.create(
                profile=profile,
                visit=visit,
                action_type="call",
                action_value=item["phone"],
            )

        self.stdout.write(self.style.SUCCESS("Demo data seeded."))
