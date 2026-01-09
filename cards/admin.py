from django.contrib import admin

from .models import Action, Customer, EditLog, Order, Payment, Profile, Visit
from .services import finalize_payment


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "package", "status", "user", "created_at")
    search_fields = ("full_name", "email", "phone")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("code", "slug", "customer", "status", "hosting_expires_at")
    search_fields = ("code", "slug", "customer__full_name")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "package", "status", "created_at")
    list_filter = ("status", "package")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "status", "amount", "currency", "created_at")
    list_filter = ("status",)
    actions = ["mark_success"]

    def mark_success(self, request, queryset):
        for payment in queryset:
            finalize_payment(payment)
        self.message_user(request, "Selected payments marked as success.")


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("profile", "visited_at", "device_type")
    list_filter = ("device_type",)


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ("profile", "action_type", "created_at")
    list_filter = ("action_type",)


@admin.register(EditLog)
class EditLogAdmin(admin.ModelAdmin):
    list_display = ("profile", "edit_type", "made_by", "created_at")
    list_filter = ("edit_type",)
