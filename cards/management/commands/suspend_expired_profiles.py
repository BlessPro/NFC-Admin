from django.core.management.base import BaseCommand
from django.utils import timezone

from cards.models import Profile


class Command(BaseCommand):
    help = "Suspend expired profiles"

    def handle(self, *args, **options):
        now = timezone.now()
        expired = Profile.objects.filter(hosting_expires_at__lt=now, status="live")
        count = expired.update(status="suspended")
        self.stdout.write(self.style.SUCCESS(f"Suspended {count} expired profiles."))
