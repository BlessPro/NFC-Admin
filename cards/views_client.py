from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from .forms import ClientLoginForm, ClientPasswordChangeForm, ClientProfileForm
from .models import Action, Profile, Visit


class ClientRequiredMixin(LoginRequiredMixin):
    login_url = "/client/login/"

    def dispatch(self, request, *args, **kwargs):
        if not getattr(request.user, "customer", None):
            return redirect("client-login")
        return super().dispatch(request, *args, **kwargs)


class ClientLoginView(LoginView):
    template_name = "client/login.html"
    authentication_form = ClientLoginForm
    redirect_authenticated_user = False

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and getattr(request.user, "customer", None):
            return redirect("client-dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return self.get_redirect_url() or "/client/"


class ClientLogoutView(LogoutView):
    next_page = "/client/login/"
    http_method_names = ["get", "post", "options"]

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class ClientDashboardView(ClientRequiredMixin, TemplateView):
    template_name = "client/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.request.user.customer
        profile = customer.profile
        now = timezone.now()
        last_7 = now - timedelta(days=7)
        visits_qs = Visit.objects.filter(profile=profile)
        actions_qs = Action.objects.filter(profile=profile)
        visits_by_day = (
            visits_qs.filter(visited_at__gte=last_7)
            .annotate(day=TruncDate("visited_at"))
            .values("day")
            .annotate(total=Count("id"))
            .order_by("day")
        )
        actions_by_type = (
            actions_qs.values("action_type").annotate(total=Count("id")).order_by("-total")
        )
        context.update(
            {
                "customer": customer,
                "profile": profile,
                "total_visits": visits_qs.count(),
                "total_actions": actions_qs.count(),
                "visits_last_7": visits_qs.filter(visited_at__gte=last_7).count(),
                "actions_last_7": actions_qs.filter(created_at__gte=last_7).count(),
                "visits_by_day": visits_by_day,
                "actions_by_type": actions_by_type,
            }
        )
        return context


class ClientProfileEditView(ClientRequiredMixin, View):
    template_name = "client/profile_edit.html"

    def get(self, request):
        profile = request.user.customer.profile
        form = ClientProfileForm(profile=profile)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "profile": profile,
                "content": profile.content_json or {},
                "theme": profile.theme_json or {},
            },
        )

    def post(self, request):
        profile = request.user.customer.profile
        form = ClientProfileForm(request.POST, request.FILES, profile=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("client-dashboard")
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "profile": profile,
                "content": profile.content_json or {},
                "theme": profile.theme_json or {},
            },
        )


class ClientPasswordChangeView(ClientRequiredMixin, PasswordChangeView):
    template_name = "client/password_change.html"
    form_class = ClientPasswordChangeForm

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Password updated.")
        return response

    def get_success_url(self):
        return "/client/"
