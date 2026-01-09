import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from .constants import HOSTING_INCLUDED_YEARS, PACKAGES
from .models import Customer, Profile, Order, Payment, EditLog

DEFAULT_THEME = {
    "mode": "light",
    "primary": "#0d6efd",
    "secondary": "#1f2937",
    "accent": "#f59e0b",
}


def generate_profile_code(length=8):
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_unique_code():
    while True:
        code = generate_profile_code()
        if not Profile.objects.filter(code=code).exists():
            return code


def generate_unique_slug(name):
    base = slugify(name) or "profile"
    base = base[:50]
    reserved = {
        "admin",
        "client",
        "order",
        "orders",
        "profile",
        "profiles",
        "c",
        "login",
        "logout",
        "dj-admin",
    }
    if base in reserved:
        base = f"{base}-card"
    slug = base
    suffix = 1
    while Profile.objects.filter(slug=slug).exists():
        slug = f"{base}-{suffix}"
        suffix += 1
    return slug


def build_theme(data):
    return {
        "mode": data.get("mode", DEFAULT_THEME["mode"]),
        "primary": data.get("primary", DEFAULT_THEME["primary"]),
        "secondary": data.get("secondary", DEFAULT_THEME["secondary"]),
        "accent": data.get("accent", DEFAULT_THEME["accent"]),
    }


def build_content(data):
    return {
        "full_name": data.get("full_name", ""),
        "title": data.get("title", ""),
        "company": data.get("company", ""),
        "phone": data.get("phone", ""),
        "whatsapp": data.get("whatsapp", ""),
        "email": data.get("email", ""),
        "website": data.get("website", ""),
        "bio": data.get("bio", ""),
        "links": data.get("links", []),
    }


def card_quantity_for_package(package_key):
    return PACKAGES.get(package_key, {}).get("card_quantity", 3)


def edits_limit_for_package(package_key):
    return PACKAGES.get(package_key, {}).get("edits_included")


def edits_remaining(profile):
    limit = edits_limit_for_package(profile.customer.package)
    if limit is None:
        return None
    used = EditLog.objects.filter(profile=profile).count()
    remaining = max(limit - used, 0)
    return remaining


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def hash_ip(ip_address):
    return hashlib.sha256(ip_address.encode("utf-8")).hexdigest() if ip_address else ""


def detect_device_type(user_agent):
    if not user_agent:
        return "unknown"
    agent = user_agent.lower()
    if "mobile" in agent or "android" in agent or "iphone" in agent:
        return "mobile"
    if "ipad" in agent or "tablet" in agent:
        return "tablet"
    return "desktop"


def _send_client_welcome_email(customer, username, raw_password):
    if not customer.email or not raw_password:
        return
    login_url = f"{settings.SITE_URL}/client/login/"
    subject = "Your ThinkTech BizCards portal login"
    message = (
        f"Hi {customer.full_name},\n\n"
        "Your client portal is ready.\n"
        f"Login: {login_url}\n"
        f"Email: {username}\n"
        f"Temporary password: {raw_password}\n\n"
        "Please change your password after logging in."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [customer.email], fail_silently=True)


def create_customer_user(customer, send_email=True):
    if not customer.email:
        return None, None
    User = get_user_model()
    existing = User.objects.filter(username=customer.email).first()
    if existing:
        customer.user = existing
        customer.save(update_fields=["user"])
        return existing, None

    raw_password = secrets.token_urlsafe(8)
    user = User.objects.create_user(
        username=customer.email,
        email=customer.email,
        password=raw_password,
        first_name=customer.full_name.split(" ")[0] if customer.full_name else "",
        last_name=" ".join(customer.full_name.split(" ")[1:]) if customer.full_name else "",
    )
    customer.user = user
    customer.save(update_fields=["user"])
    if send_email:
        _send_client_welcome_email(customer, user.username, raw_password)
    return user, raw_password


@transaction.atomic
def finalize_payment(payment):
    if payment.status == "success" and payment.order_id and payment.customer_id:
        return payment.order

    payload = payment.raw_payload or {}
    package = payload.get("package", "basic")
    customer_data = payload.get("customer", {})
    shipping_data = payload.get("shipping", {})
    content_data = payload.get("content", {})
    theme_data = payload.get("theme", {})
    template_key = payload.get("template_key", "business")

    customer = Customer.objects.create(
        full_name=customer_data.get("full_name", ""),
        email=customer_data.get("email", ""),
        phone=customer_data.get("phone", ""),
        package=package,
        status="active",
    )

    content = build_content(content_data)
    theme = build_theme(theme_data)
    display_name = content.get("full_name") or customer.full_name

    profile = Profile.objects.create(
        customer=customer,
        code=generate_unique_code(),
        slug=generate_unique_slug(display_name),
        template_key=template_key,
        theme_json=theme,
        content_json=content,
        status="live",
        hosting_expires_at=timezone.now() + timedelta(days=365 * HOSTING_INCLUDED_YEARS),
    )

    order = Order.objects.create(
        customer=customer,
        profile=profile,
        package=package,
        card_quantity=card_quantity_for_package(package),
        shipping_name=shipping_data.get("shipping_name", customer.full_name),
        shipping_phone=shipping_data.get("shipping_phone", customer.phone),
        shipping_address=shipping_data.get("shipping_address", ""),
        status="paid",
        paid_at=timezone.now(),
    )

    create_customer_user(customer, send_email=True)

    payment.customer = customer
    payment.order = order
    payment.status = "success"
    payment.amount = payment.amount or PACKAGES.get(package, {}).get("price", 0)
    payment.currency = payment.currency or "GHS"
    payment.paid_at = timezone.now()
    payment.save()

    return order
