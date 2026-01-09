from django.urls import path

from . import views_admin

urlpatterns = [
    path("login/", views_admin.AdminLoginView.as_view(), name="admin-login"),
    path("logout/", views_admin.AdminLogoutView.as_view(), name="admin-logout"),
    path("", views_admin.AdminDashboardView.as_view(), name="admin-dashboard"),
    path("customers/", views_admin.CustomersListView.as_view(), name="admin-customers"),
    path("customers/<int:pk>/", views_admin.CustomerDetailView.as_view(), name="admin-customer-detail"),
    path("profiles/", views_admin.ProfilesListView.as_view(), name="admin-profiles"),
    path("profiles/<int:pk>/", views_admin.ProfileDetailView.as_view(), name="admin-profile-detail"),
    path("profiles/<int:pk>/edit/", views_admin.ProfileEditView.as_view(), name="admin-profile-edit"),
    path("orders/", views_admin.OrdersListView.as_view(), name="admin-orders"),
    path("orders/<int:pk>/", views_admin.OrderDetailView.as_view(), name="admin-order-detail"),
    path("analytics/", views_admin.AnalyticsView.as_view(), name="admin-analytics"),
    path("analytics/profiles/<int:pk>/", views_admin.ProfileAnalyticsView.as_view(), name="admin-profile-analytics"),
    path("renewals/", views_admin.RenewalsView.as_view(), name="admin-renewals"),
    path("renewals/<int:pk>/extend/", views_admin.RenewalExtendView.as_view(), name="admin-renewals-extend"),
    path("settings/", views_admin.SettingsView.as_view(), name="admin-settings"),
]
