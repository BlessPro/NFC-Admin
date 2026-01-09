from django.conf import settings
from django.db import models
from django.utils import timezone

from .constants import (
    CUSTOMER_STATUS_CHOICES,
    ORDER_STATUS_CHOICES,
    PACKAGE_CHOICES,
    PAYMENT_STATUS_CHOICES,
    PROFILE_STATUS_CHOICES,
    TEMPLATE_CHOICES,
)


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Customer(TimestampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer",
    )
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    package = models.CharField(max_length=20, choices=PACKAGE_CHOICES)
    status = models.CharField(max_length=20, choices=CUSTOMER_STATUS_CHOICES, default="active")

    def __str__(self):
        return f"{self.full_name} ({self.package})"


class Profile(TimestampedModel):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name="profile")
    code = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=80, unique=True, null=True, blank=True)
    template_key = models.CharField(max_length=30, choices=TEMPLATE_CHOICES, default="business")
    theme_json = models.JSONField(default=dict)
    content_json = models.JSONField(default=dict)
    logo = models.ImageField(upload_to="logos/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=PROFILE_STATUS_CHOICES, default="draft")
    hosting_expires_at = models.DateTimeField()

    def __str__(self):
        return f"{self.customer.full_name} - {self.code}"

    @property
    def is_expired(self):
        return self.hosting_expires_at and self.hosting_expires_at < timezone.now()

    @property
    def is_active(self):
        return self.status == "live" and not self.is_expired

    def public_url(self):
        return f"/c/{self.code}"

    def nice_url(self):
        if self.slug:
            return f"/{self.slug}"
        return None


class Order(TimestampedModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="orders")
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="orders")
    package = models.CharField(max_length=20, choices=PACKAGE_CHOICES)
    card_quantity = models.PositiveIntegerField(default=1)
    shipping_name = models.CharField(max_length=120)
    shipping_phone = models.CharField(max_length=30)
    shipping_address = models.TextField()
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default="paid")
    paid_at = models.DateTimeField(null=True, blank=True)
    encoded_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    tracking_code = models.CharField(max_length=80, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Order {self.id} - {self.customer.full_name}"


class Payment(TimestampedModel):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    provider = models.CharField(max_length=40)
    reference = models.CharField(max_length=60, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="GHS")
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending")
    paid_at = models.DateTimeField(null=True, blank=True)
    raw_payload = models.JSONField(default=dict)

    def __str__(self):
        return f"Payment {self.reference} ({self.status})"


class Visit(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="visits")
    visited_at = models.DateTimeField(default=timezone.now)
    ip_hash = models.CharField(max_length=64)
    user_agent = models.TextField(null=True, blank=True)
    referrer = models.TextField(null=True, blank=True)
    utm_source = models.CharField(max_length=120, null=True, blank=True)
    utm_medium = models.CharField(max_length=120, null=True, blank=True)
    utm_campaign = models.CharField(max_length=120, null=True, blank=True)
    utm_term = models.CharField(max_length=120, null=True, blank=True)
    utm_content = models.CharField(max_length=120, null=True, blank=True)
    device_type = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Visit {self.profile.code} at {self.visited_at}"


class Action(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="actions")
    visit = models.ForeignKey(Visit, on_delete=models.SET_NULL, null=True, blank=True, related_name="actions")
    action_type = models.CharField(max_length=40)
    action_value = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action_type} - {self.profile.code}"


class EditLog(models.Model):
    EDIT_TYPE_CHOICES = [
        ("content", "Content"),
        ("theme", "Theme"),
        ("template", "Template"),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="edit_logs")
    made_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profile_edit_logs",
    )
    edit_type = models.CharField(max_length=20, choices=EDIT_TYPE_CHOICES)
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Edit {self.edit_type} for {self.profile.code}"
