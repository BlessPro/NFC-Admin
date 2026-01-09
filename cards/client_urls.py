from django.urls import path

from . import views_client

urlpatterns = [
    path("login/", views_client.ClientLoginView.as_view(), name="client-login"),
    path("logout/", views_client.ClientLogoutView.as_view(), name="client-logout"),
    path("", views_client.ClientDashboardView.as_view(), name="client-dashboard"),
    path("profile/", views_client.ClientProfileEditView.as_view(), name="client-profile-edit"),
    path("password/", views_client.ClientPasswordChangeView.as_view(), name="client-password-change"),
]
