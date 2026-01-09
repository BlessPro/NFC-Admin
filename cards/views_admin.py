from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from .constants import HOSTING_PRICE_YEARLY, PACKAGES
from .forms import AdminLoginForm, OrderStatusForm, ProfileEditForm
from .models import Action, Customer, EditLog, Order, Profile, Visit
from .services import edits_remaining


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class AdminNavMixin:
    active_nav = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_nav"] = self.active_nav
        return context


class AdminLoginView(LoginView):
    template_name = "ops/login.html"
    authentication_form = AdminLoginForm


class AdminLogoutView(LogoutView):
    pass


class AdminDashboardView(AdminRequiredMixin, AdminNavMixin, TemplateView):
    template_name = "ops/dashboard.html"
    active_nav = "dashboard"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        last_7 = now - timedelta(days=7)
        context.update(
            {
                "new_paid_orders": Order.objects.filter(status="paid").count(),
                "orders_to_encode": Order.objects.filter(status="paid").count(),
                "orders_to_ship": Order.objects.filter(status="encoded").count(),
                "profiles_live": Profile.objects.filter(
                    status="live", hosting_expires_at__gte=now
                ).count(),
                "renewals_30d": Profile.objects.filter(
                    hosting_expires_at__lte=now + timedelta(days=30),
                    hosting_expires_at__gte=now,
                ).count(),
                "renewals_7d": Profile.objects.filter(
                    hosting_expires_at__lte=now + timedelta(days=7),
                    hosting_expires_at__gte=now,
                ).count(),
                "visits_last_7d": Visit.objects.filter(visited_at__gte=last_7).count(),
                "actions_last_7d": Action.objects.filter(created_at__gte=last_7).count(),
            }
        )
        return context


class CustomersListView(AdminRequiredMixin, AdminNavMixin, ListView):
    template_name = "ops/customers_list.html"
    model = Customer
    context_object_name = "customers"
    active_nav = "customers"

    def get_queryset(self):
        return Customer.objects.select_related("profile").order_by("-created_at")


class CustomerDetailView(AdminRequiredMixin, AdminNavMixin, DetailView):
    template_name = "ops/customer_detail.html"
    model = Customer
    context_object_name = "customer"
    active_nav = "customers"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["orders"] = self.object.orders.select_related("profile").order_by("-created_at")
        return context


class ProfilesListView(AdminRequiredMixin, AdminNavMixin, ListView):
    template_name = "ops/profiles_list.html"
    model = Profile
    context_object_name = "profiles"
    active_nav = "profiles"

    def get_queryset(self):
        return Profile.objects.select_related("customer").order_by("-created_at")


class ProfileDetailView(AdminRequiredMixin, AdminNavMixin, DetailView):
    template_name = "ops/profile_detail.html"
    model = Profile
    context_object_name = "profile"
    active_nav = "profiles"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["edits_remaining"] = edits_remaining(self.object)
        context["edit_logs"] = self.object.edit_logs.select_related("made_by").order_by("-created_at")[:10]
        return context


class ProfileEditView(AdminRequiredMixin, AdminNavMixin, View):
    template_name = "ops/profile_edit.html"
    active_nav = "profiles"

    def get(self, request, pk):
        profile = get_object_or_404(Profile, pk=pk)
        form = ProfileEditForm(profile=profile)
        return render(
            request,
            self.template_name,
            {
                "profile": profile,
                "form": form,
                "content": profile.content_json or {},
                "theme": profile.theme_json or {},
                "active_nav": self.active_nav,
            },
        )

    def post(self, request, pk):
        profile = get_object_or_404(Profile, pk=pk)
        form = ProfileEditForm(request.POST, request.FILES, profile=profile)
        if form.is_valid():
            changed_fields = form.changed_data
            form.save()
            edit_type = "content"
            if "template_key" in changed_fields:
                edit_type = "template"
            elif any(field in changed_fields for field in ["mode", "primary", "secondary", "accent"]):
                edit_type = "theme"
            EditLog.objects.create(
                profile=profile,
                made_by=request.user,
                edit_type=edit_type,
                summary="Updated profile settings",
            )
            messages.success(request, "Profile updated.")
            return redirect("admin-profile-detail", pk=profile.pk)
        return render(
            request,
            self.template_name,
            {
                "profile": profile,
                "form": form,
                "content": profile.content_json or {},
                "theme": profile.theme_json or {},
                "active_nav": self.active_nav,
            },
        )


class OrdersListView(AdminRequiredMixin, AdminNavMixin, ListView):
    template_name = "ops/orders_list.html"
    model = Order
    context_object_name = "orders"
    active_nav = "orders"

    def get_queryset(self):
        return Order.objects.select_related("customer", "profile").order_by("-created_at")


class OrderDetailView(AdminRequiredMixin, AdminNavMixin, View):
    template_name = "ops/order_detail.html"
    active_nav = "orders"

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        form = OrderStatusForm(
            initial={
                "status": order.status,
                "tracking_code": order.tracking_code,
                "notes": order.notes,
            }
        )
        return render(
            request,
            self.template_name,
            {"order": order, "form": form, "active_nav": self.active_nav},
        )

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        form = OrderStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data["status"]
            order.status = status
            order.tracking_code = form.cleaned_data["tracking_code"]
            order.notes = form.cleaned_data["notes"]
            now = timezone.now()
            if status == "paid" and not order.paid_at:
                order.paid_at = now
            if status == "encoded" and not order.encoded_at:
                order.encoded_at = now
            if status == "shipped" and not order.shipped_at:
                order.shipped_at = now
            order.save()
            messages.success(request, "Order updated.")
            return redirect("admin-order-detail", pk=order.pk)
        return render(
            request,
            self.template_name,
            {"order": order, "form": form, "active_nav": self.active_nav},
        )


class AnalyticsView(AdminRequiredMixin, AdminNavMixin, TemplateView):
    template_name = "ops/analytics.html"
    active_nav = "analytics"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_visits"] = Visit.objects.count()
        context["total_actions"] = Action.objects.count()
        context["top_actions"] = (
            Action.objects.values("action_type")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
        return context


class ProfileAnalyticsView(AdminRequiredMixin, AdminNavMixin, TemplateView):
    template_name = "ops/profile_analytics.html"
    active_nav = "analytics"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_object_or_404(Profile, pk=kwargs.get("pk"))
        visits_qs = Visit.objects.filter(profile=profile)
        actions_qs = Action.objects.filter(profile=profile)
        visits_by_day = (
            visits_qs.annotate(day=TruncDate("visited_at"))
            .values("day")
            .annotate(total=Count("id"))
            .order_by("-day")
        )
        actions_breakdown = (
            actions_qs.values("action_type")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
        total_visits = visits_qs.count()
        total_actions = actions_qs.count()
        conversion_rate = (total_actions / total_visits) if total_visits else 0
        context.update(
            {
                "profile": profile,
                "visits_by_day": visits_by_day,
                "actions_breakdown": actions_breakdown,
                "total_visits": total_visits,
                "total_actions": total_actions,
                "conversion_rate": conversion_rate,
            }
        )
        return context


class RenewalsView(AdminRequiredMixin, AdminNavMixin, TemplateView):
    template_name = "ops/renewals.html"
    active_nav = "renewals"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        context["expiring_7"] = Profile.objects.filter(
            hosting_expires_at__lte=now + timedelta(days=7),
            hosting_expires_at__gte=now,
        ).select_related("customer")
        context["expiring_30"] = Profile.objects.filter(
            hosting_expires_at__lte=now + timedelta(days=30),
            hosting_expires_at__gt=now + timedelta(days=7),
        ).select_related("customer")
        context["expired"] = Profile.objects.filter(hosting_expires_at__lt=now).select_related("customer")
        return context


class RenewalExtendView(AdminRequiredMixin, View):
    def post(self, request, pk):
        profile = get_object_or_404(Profile, pk=pk)
        now = timezone.now()
        base = profile.hosting_expires_at if profile.hosting_expires_at > now else now
        profile.hosting_expires_at = base + timedelta(days=365)
        profile.status = "live"
        profile.save()
        messages.success(request, "Hosting extended by 1 year.")
        return redirect("admin-renewals")


class SettingsView(AdminRequiredMixin, AdminNavMixin, TemplateView):
    template_name = "ops/settings.html"
    active_nav = "settings"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["packages"] = PACKAGES
        context["hosting_price"] = HOSTING_PRICE_YEARLY
        return context
