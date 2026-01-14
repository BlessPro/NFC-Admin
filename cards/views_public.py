import io
import uuid

from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import FormView, TemplateView
import qrcode


from .constants import PACKAGES
from .forms import OrderCreateForm
from .models import Action, Payment, Profile, Visit
from .services import detect_device_type, finalize_payment, get_client_ip, hash_ip


class HomeView(TemplateView):
    template_name = "public/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["packages"] = PACKAGES
        return context


class OrderCreateView(FormView):
    template_name = "order/create.html"
    form_class = OrderCreateForm

    def form_valid(self, form):
        payload = form.build_payload()
        package = payload.get("package")
        payment = Payment.objects.create(
            provider="manual",
            reference=uuid.uuid4().hex,
            amount=PACKAGES.get(package, {}).get("price", 0),
            currency="GHS",
            status="pending",
            raw_payload=payload,
        )
        return redirect("order-confirm", reference=payment.reference)


def order_confirm(request, reference):
    payment = get_object_or_404(Payment, reference=reference)
    payload = payment.raw_payload or {}
    if request.method == "POST":
        finalize_payment(payment)
        return redirect("order-success", reference=reference)
    return render(
        request,
        "order/confirm.html",
        {
            "payment": payment,
            "payload": payload,
            "package": PACKAGES.get(payload.get("package"), {}),
        },
    )


def order_success(request, reference):
    payment = get_object_or_404(Payment, reference=reference)
    order = payment.order
    if not order:
        return redirect("order-confirm", reference=reference)
    return render(
        request,
        "order/success.html",
        {
            "payment": payment,
            "order": order,
            "profile": order.profile,
        },
    )


def _build_vcard(profile):
    content = profile.content_json or {}
    full_name = content.get("full_name", "")
    phone = content.get("phone", "")
    email = content.get("email", "")
    website = content.get("website", "")

    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"FN:{full_name}",
    ]
    if phone:
        lines.append(f"TEL;TYPE=CELL:{phone}")
    if email:
        lines.append(f"EMAIL:{email}")
    if website:
        lines.append(f"URL:{website}")
    lines.append("END:VCARD")
    return "\r\n".join(lines)


def _build_qr_png(data):
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def profile_vcard(request, code):
    profile = get_object_or_404(Profile, code=code)
    vcard = _build_vcard(profile)
    filename = profile.slug or profile.code
    response = HttpResponse(vcard, content_type="text/vcard; charset=utf-8")
    response["Content-Disposition"] = f"attachment; filename=\"{filename}.vcf\""
    return response


def profile_qr(request, code):
    profile = get_object_or_404(Profile, code=code)
    qr_type = (request.GET.get("type") or "vcard").lower()
    content = profile.content_json or {}
    if qr_type == "call":
        phone = content.get("phone") or content.get("whatsapp")
        if not phone:
            return HttpResponseBadRequest("phone-missing")
        data = f"tel:{phone}"
    elif qr_type in {"vcard", "contact", "save"}:
        data = _build_vcard(profile)
    elif qr_type == "url":
        data = request.build_absolute_uri(reverse("profile-by-code", args=[profile.code]))
    else:
        return HttpResponseBadRequest("invalid-type")

    png = _build_qr_png(data)
    response = HttpResponse(png, content_type="image/png")
    response["Cache-Control"] = "no-store"
    return response


def _log_visit(request, profile):
    ip = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    return Visit.objects.create(
        profile=profile,
        visited_at=timezone.now(),
        ip_hash=hash_ip(ip),
        user_agent=user_agent,
        referrer=request.META.get("HTTP_REFERER", ""),
        utm_source=request.GET.get("utm_source"),
        utm_medium=request.GET.get("utm_medium"),
        utm_campaign=request.GET.get("utm_campaign"),
        utm_term=request.GET.get("utm_term"),
        utm_content=request.GET.get("utm_content"),
        device_type=detect_device_type(user_agent),
    )


def _render_profile(request, profile):
    if not profile.is_active:
        return render(request, "profiles/inactive.html", {"profile": profile})

    visit = _log_visit(request, profile)
    return render(
        request,
        "profiles/profile.html",
        {
            "profile": profile,
            "content": profile.content_json or {},
            "theme": profile.theme_json or {},
            "visit_id": visit.id,
            "action_url": reverse("profile-action", args=[profile.code]),
            "vcard_url": reverse("profile-vcard", args=[profile.code]),
        },
    )


def profile_by_code(request, code):
    profile = get_object_or_404(Profile, code=code)
    return _render_profile(request, profile)


def profile_by_slug(request, slug):
    profile = get_object_or_404(Profile, slug=slug)
    return _render_profile(request, profile)


@csrf_exempt
@require_POST
def profile_action(request, code):
    profile = get_object_or_404(Profile, code=code)
    if not profile.is_active:
        return JsonResponse({"ok": False, "error": "inactive"}, status=400)
    action_type = request.POST.get("action_type")
    action_value = request.POST.get("action_value", "")
    visit_id = request.POST.get("visit_id")
    visit = None
    if visit_id:
        visit = Visit.objects.filter(id=visit_id, profile=profile).first()
    if action_type:
        Action.objects.create(
            profile=profile,
            visit=visit,
            action_type=action_type,
            action_value=action_value,
        )
    return JsonResponse({"ok": True})
