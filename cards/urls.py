from django.urls import path

from . import views_public

urlpatterns = [
    path("", views_public.HomeView.as_view(), name="home"),
    path("order/", views_public.OrderCreateView.as_view(), name="order-create"),
    path("order/confirm/<str:reference>/", views_public.order_confirm, name="order-confirm"),
    path("order/success/<str:reference>/", views_public.order_success, name="order-success"),
    path("c/<str:code>/card.vcf", views_public.profile_vcard, name="profile-vcard"),
    path("c/<str:code>/action", views_public.profile_action, name="profile-action"),
    path("c/<str:code>/", views_public.profile_by_code, name="profile-by-code"),
    path("<slug:slug>/", views_public.profile_by_slug, name="profile-by-slug"),
]
