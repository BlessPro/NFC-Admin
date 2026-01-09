from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("full_name", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(max_length=30)),
                (
                    "package",
                    models.CharField(
                        choices=[("basic", "Basic"), ("pro", "Pro"), ("premium", "Premium")],
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Active"), ("suspended", "Suspended")],
                        default="active",
                        max_length=20,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(max_length=20, unique=True)),
                ("slug", models.SlugField(blank=True, max_length=80, null=True, unique=True)),
                (
                    "template_key",
                    models.CharField(
                        choices=[
                            ("business", "Business"),
                            ("portfolio", "Portfolio"),
                            ("music", "Music"),
                            ("restaurant", "Restaurant"),
                        ],
                        default="business",
                        max_length=30,
                    ),
                ),
                ("theme_json", models.JSONField(default=dict)),
                ("content_json", models.JSONField(default=dict)),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "Draft"), ("live", "Live"), ("suspended", "Suspended")],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("hosting_expires_at", models.DateTimeField()),
                (
                    "customer",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to="cards.customer",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "package",
                    models.CharField(
                        choices=[("basic", "Basic"), ("pro", "Pro"), ("premium", "Premium")],
                        max_length=20,
                    ),
                ),
                ("card_quantity", models.PositiveIntegerField(default=1)),
                ("shipping_name", models.CharField(max_length=120)),
                ("shipping_phone", models.CharField(max_length=30)),
                ("shipping_address", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("paid", "Paid"),
                            ("encoded", "Encoded"),
                            ("shipped", "Shipped"),
                            ("completed", "Completed"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="paid",
                        max_length=20,
                    ),
                ),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("encoded_at", models.DateTimeField(blank=True, null=True)),
                ("shipped_at", models.DateTimeField(blank=True, null=True)),
                ("tracking_code", models.CharField(blank=True, max_length=80, null=True)),
                ("notes", models.TextField(blank=True, null=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="orders",
                        to="cards.customer",
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="orders",
                        to="cards.profile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("provider", models.CharField(max_length=40)),
                ("reference", models.CharField(max_length=60, unique=True)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("currency", models.CharField(default="GHS", max_length=10)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("success", "Success"),
                            ("failed", "Failed"),
                            ("refunded", "Refunded"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("raw_payload", models.JSONField(default=dict)),
                (
                    "customer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="payments",
                        to="cards.customer",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="payments",
                        to="cards.order",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Visit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("visited_at", models.DateTimeField()),
                ("ip_hash", models.CharField(max_length=64)),
                ("user_agent", models.TextField(blank=True, null=True)),
                ("referrer", models.TextField(blank=True, null=True)),
                ("utm_source", models.CharField(blank=True, max_length=120, null=True)),
                ("utm_medium", models.CharField(blank=True, max_length=120, null=True)),
                ("utm_campaign", models.CharField(blank=True, max_length=120, null=True)),
                ("utm_term", models.CharField(blank=True, max_length=120, null=True)),
                ("utm_content", models.CharField(blank=True, max_length=120, null=True)),
                ("device_type", models.CharField(blank=True, max_length=40, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="visits",
                        to="cards.profile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Action",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action_type", models.CharField(max_length=40)),
                ("action_value", models.CharField(blank=True, max_length=255, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="actions",
                        to="cards.profile",
                    ),
                ),
                (
                    "visit",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="actions",
                        to="cards.visit",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="EditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "edit_type",
                    models.CharField(
                        choices=[("content", "Content"), ("theme", "Theme"), ("template", "Template")],
                        max_length=20,
                    ),
                ),
                ("summary", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "made_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="profile_edit_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="edit_logs",
                        to="cards.profile",
                    ),
                ),
            ],
        ),
    ]
