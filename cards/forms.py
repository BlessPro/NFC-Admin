from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from .constants import PACKAGE_CHOICES, PROFILE_STATUS_CHOICES, TEMPLATE_CHOICES
from .services import build_content, build_theme


def _apply_bootstrap(field):
    widget = field.widget
    base = (
        "w-full rounded-xl border border-slate-700 bg-slate-900/70 "
        "px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 "
        "focus:border-tt-accent focus:outline-none focus:ring-2 focus:ring-tt-accent/40"
    )
    if isinstance(widget, forms.Select):
        css_class = base
    elif isinstance(widget, (forms.CheckboxInput, forms.RadioSelect)):
        css_class = "h-4 w-4 rounded border-slate-700 bg-slate-900 text-tt-accent focus:ring-tt-accent/40"
    elif isinstance(widget, forms.ClearableFileInput):
        css_class = (
            "w-full rounded-xl border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 "
            "file:mr-4 file:rounded-full file:border-0 file:bg-tt-accent file:px-4 file:py-2 "
            "file:text-xs file:font-semibold file:text-slate-950"
        )
    else:
        css_class = base
        if widget.attrs.get("type") == "color":
            css_class = "h-10 w-16 rounded-lg border border-slate-700 bg-slate-900/70 p-1"
    widget.attrs.setdefault("class", css_class)


def _to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class AdminLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            _apply_bootstrap(field)


class ClientLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Email"
        for field in self.fields.values():
            _apply_bootstrap(field)
        login_class = (
            "w-full rounded-full border border-emerald-900/60 bg-emerald-950/60 "
            "px-4 py-2 text-sm text-emerald-50 placeholder:text-emerald-200/60 "
            "focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-400/40"
        )
        for field in self.fields.values():
            field.widget.attrs["class"] = login_class
        self.fields["username"].widget.attrs.setdefault("placeholder", "Enter your email")
        self.fields["username"].widget.attrs.setdefault("autofocus", "autofocus")
        self.fields["password"].widget.attrs.setdefault("placeholder", "Enter your password")


class OrderCreateForm(forms.Form):
    full_name = forms.CharField(max_length=120)
    email = forms.EmailField()
    phone = forms.CharField(max_length=30)
    package = forms.ChoiceField(choices=PACKAGE_CHOICES)

    shipping_name = forms.CharField(max_length=120)
    shipping_phone = forms.CharField(max_length=30)
    shipping_address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))

    template_key = forms.ChoiceField(choices=TEMPLATE_CHOICES)
    mode = forms.ChoiceField(choices=[("light", "Light"), ("dark", "Dark")])
    primary = forms.CharField(widget=forms.TextInput(attrs={"type": "color"}))
    secondary = forms.CharField(widget=forms.TextInput(attrs={"type": "color"}))
    accent = forms.CharField(widget=forms.TextInput(attrs={"type": "color"}))

    title = forms.CharField(max_length=120, required=False)
    company = forms.CharField(max_length=120, required=False)
    whatsapp = forms.CharField(max_length=30, required=False)
    website = forms.CharField(max_length=200, required=False)
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    links_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Label | https://example.com"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["primary"].initial = "#0d6efd"
        self.fields["secondary"].initial = "#1f2937"
        self.fields["accent"].initial = "#f59e0b"
        for field in self.fields.values():
            _apply_bootstrap(field)

    def _parse_links(self, text):
        links = []
        for line in (text or "").splitlines():
            line = line.strip()
            if not line:
                continue
            if "|" in line:
                label, url = [part.strip() for part in line.split("|", 1)]
            else:
                label, url = line, line
            links.append({"label": label, "url": url})
        return links

    def build_payload(self):
        data = self.cleaned_data
        links = self._parse_links(data.get("links_text"))
        customer = {
            "full_name": data.get("full_name"),
            "email": data.get("email"),
            "phone": data.get("phone"),
        }
        content = build_content(
            {
                "full_name": data.get("full_name"),
                "title": data.get("title"),
                "company": data.get("company"),
                "phone": data.get("phone"),
                "whatsapp": data.get("whatsapp") or data.get("phone"),
                "email": data.get("email"),
                "website": data.get("website"),
                "bio": data.get("bio"),
                "links": links,
            }
        )
        theme = build_theme(
            {
                "mode": data.get("mode"),
                "primary": data.get("primary"),
                "secondary": data.get("secondary"),
                "accent": data.get("accent"),
            }
        )
        shipping = {
            "shipping_name": data.get("shipping_name"),
            "shipping_phone": data.get("shipping_phone"),
            "shipping_address": data.get("shipping_address"),
        }

        return {
            "package": data.get("package"),
            "customer": customer,
            "shipping": shipping,
            "template_key": data.get("template_key"),
            "theme": theme,
            "content": content,
        }


class ProfileEditForm(forms.Form):
    template_key = forms.ChoiceField(choices=TEMPLATE_CHOICES)
    status = forms.ChoiceField(choices=PROFILE_STATUS_CHOICES)
    mode = forms.ChoiceField(choices=[("light", "Light"), ("dark", "Dark")])
    primary = forms.CharField(widget=forms.TextInput(attrs={"type": "color"}))
    secondary = forms.CharField(widget=forms.TextInput(attrs={"type": "color"}))
    accent = forms.CharField(widget=forms.TextInput(attrs={"type": "color"}))
    logo = forms.ImageField(required=False)

    full_name = forms.CharField(max_length=120)
    title = forms.CharField(max_length=120, required=False)
    company = forms.CharField(max_length=120, required=False)
    phone = forms.CharField(max_length=30, required=False)
    whatsapp = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    website = forms.CharField(max_length=200, required=False)
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    links_text = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop("profile", None)
        super().__init__(*args, **kwargs)
        if self.profile:
            theme = self.profile.theme_json or {}
            content = self.profile.content_json or {}
            links = content.get("links") or []
            links_text = "\n".join(
                [f"{link.get('label', '')} | {link.get('url', '')}".strip(" |") for link in links]
            )

            self.initial.update(
                {
                    "template_key": self.profile.template_key,
                    "status": self.profile.status,
                    "mode": theme.get("mode", "light"),
                    "primary": theme.get("primary", "#0d6efd"),
                    "secondary": theme.get("secondary", "#1f2937"),
                    "accent": theme.get("accent", "#f59e0b"),
                    "full_name": content.get("full_name", ""),
                    "title": content.get("title", ""),
                    "company": content.get("company", ""),
                    "phone": content.get("phone", ""),
                    "whatsapp": content.get("whatsapp", ""),
                    "email": content.get("email", ""),
                    "website": content.get("website", ""),
                    "bio": content.get("bio", ""),
                    "links_text": links_text,
                }
            )
        for field in self.fields.values():
            _apply_bootstrap(field)

    def _parse_links(self, text):
        links = []
        for line in (text or "").splitlines():
            line = line.strip()
            if not line:
                continue
            if "|" in line:
                label, url = [part.strip() for part in line.split("|", 1)]
            else:
                label, url = line, line
            links.append({"label": label, "url": url})
        return links

    def save(self):
        if not self.profile:
            raise ValueError("Profile is required")

        data = self.cleaned_data
        logo = data.get("logo")
        self.profile.template_key = data.get("template_key")
        self.profile.status = data.get("status")
        theme = self.profile.theme_json or {}
        theme.update(
            build_theme(
                {
                    "mode": data.get("mode"),
                    "primary": data.get("primary"),
                    "secondary": data.get("secondary"),
                    "accent": data.get("accent"),
                }
            )
        )
        self.profile.theme_json = theme
        self.profile.content_json = build_content(
            {
                "full_name": data.get("full_name"),
                "title": data.get("title"),
                "company": data.get("company"),
                "phone": data.get("phone"),
                "whatsapp": data.get("whatsapp"),
                "email": data.get("email"),
                "website": data.get("website"),
                "bio": data.get("bio"),
                "links": self._parse_links(data.get("links_text")),
            }
        )
        if logo:
            self.profile.logo = logo
        self.profile.save()
        return self.profile


class OrderStatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=[
            ("paid", "Paid"),
            ("encoded", "Encoded"),
            ("shipped", "Shipped"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ]
    )
    tracking_code = forms.CharField(required=False)
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            _apply_bootstrap(field)


class ClientPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            _apply_bootstrap(field)


class ClientProfileForm(forms.Form):
    logo = forms.ImageField(required=False)
    full_name = forms.CharField(max_length=120)
    title = forms.CharField(max_length=120, required=False)
    company = forms.CharField(max_length=120, required=False)
    phone = forms.CharField(max_length=30, required=False)
    whatsapp = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    website = forms.CharField(max_length=200, required=False)
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    links_text = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    layout = forms.CharField(required=False, widget=forms.HiddenInput())
    header_mode = forms.CharField(required=False, widget=forms.HiddenInput())
    header_text = forms.CharField(required=False, widget=forms.HiddenInput())
    header_font = forms.CharField(required=False, widget=forms.HiddenInput())
    link_font = forms.CharField(required=False, widget=forms.HiddenInput())
    bio_font = forms.CharField(required=False, widget=forms.HiddenInput())
    name_size = forms.CharField(required=False, widget=forms.HiddenInput())
    bio_size = forms.CharField(required=False, widget=forms.HiddenInput())
    wallpaper = forms.CharField(required=False, widget=forms.HiddenInput())
    text_color = forms.CharField(required=False, widget=forms.HiddenInput())
    button_style = forms.CharField(required=False, widget=forms.HiddenInput())
    button_radius = forms.CharField(required=False, widget=forms.HiddenInput())
    button_shadow = forms.CharField(required=False, widget=forms.HiddenInput())
    button_bg = forms.CharField(required=False, widget=forms.HiddenInput())
    button_text = forms.CharField(required=False, widget=forms.HiddenInput())
    footer_text = forms.CharField(required=False, widget=forms.HiddenInput())
    footer_show = forms.CharField(required=False, widget=forms.HiddenInput())
    primary = forms.CharField(required=False, widget=forms.HiddenInput())
    accent = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop("profile", None)
        super().__init__(*args, **kwargs)
        if self.profile:
            content = self.profile.content_json or {}
            theme = self.profile.theme_json or {}
            links = content.get("links") or []
            links_text = "\n".join(
                [f"{link.get('label', '')} | {link.get('url', '')}".strip(" |") for link in links]
            )
            self.initial.update(
                {
                    "full_name": content.get("full_name", "") or self.profile.customer.full_name,
                    "title": content.get("title", ""),
                    "company": content.get("company", ""),
                    "phone": content.get("phone", "") or self.profile.customer.phone,
                    "whatsapp": content.get("whatsapp", ""),
                    "email": content.get("email", "") or self.profile.customer.email,
                    "website": content.get("website", ""),
                    "bio": content.get("bio", ""),
                    "links_text": links_text,
                    "layout": theme.get("layout", "linktree"),
                    "header_mode": theme.get("header_mode", "image" if self.profile.logo else "text"),
                    "header_text": theme.get("header_text", "") or content.get("company") or content.get("full_name"),
                    "header_font": theme.get("header_font", "'Sora', sans-serif"),
                    "link_font": theme.get("link_font", "'Sora', sans-serif"),
                    "bio_font": theme.get("bio_font", "'Sora', sans-serif"),
                    "name_size": theme.get("name_size", "1.125rem"),
                    "bio_size": theme.get("bio_size", "0.75rem"),
                    "wallpaper": theme.get(
                        "wallpaper",
                        "linear-gradient(180deg, #0f172a 0%, #0b0f14 100%)",
                    ),
                    "text_color": theme.get("text_color", "#f8fafc"),
                    "button_style": theme.get("button_style", "solid"),
                    "button_radius": str(theme.get("button_radius", "100")),
                    "button_shadow": theme.get("button_shadow", "subtle"),
                    "button_bg": theme.get("button_bg", theme.get("primary", "#27d3a6")),
                    "button_text": theme.get("button_text", "#0b0f14"),
                    "footer_text": theme.get("footer_text", "Made by 10minal"),
                    "footer_show": str(theme.get("footer_show", True)).lower(),
                    "primary": theme.get("primary", "#27d3a6"),
                    "accent": theme.get("accent", "#f59e0b"),
                }
            )
        for field in self.fields.values():
            _apply_bootstrap(field)

    def _parse_links(self, text):
        links = []
        for line in (text or "").splitlines():
            line = line.strip()
            if not line:
                continue
            if "|" in line:
                label, url = [part.strip() for part in line.split("|", 1)]
            else:
                label, url = line, line
            links.append({"label": label, "url": url})
        return links

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email or not self.profile or not self.profile.customer.user:
            return email
        user = self.profile.customer.user
        if email.lower() != (user.email or "").lower():
            User = get_user_model()
            if User.objects.filter(username=email).exclude(pk=user.pk).exists():
                raise forms.ValidationError("That email is already in use.")
        return email

    def save(self):
        if not self.profile:
            raise ValueError("Profile is required")

        data = self.cleaned_data
        links = self._parse_links(data.get("links_text"))
        self.profile.content_json = build_content(
            {
                "full_name": data.get("full_name"),
                "title": data.get("title"),
                "company": data.get("company"),
                "phone": data.get("phone"),
                "whatsapp": data.get("whatsapp"),
                "email": data.get("email"),
                "website": data.get("website"),
                "bio": data.get("bio"),
                "links": links,
            }
        )
        theme = self.profile.theme_json or {}
        theme.update(
            build_theme(
                {
                    "mode": theme.get("mode", "light"),
                    "primary": data.get("primary") or theme.get("primary"),
                    "secondary": theme.get("secondary"),
                    "accent": data.get("accent") or theme.get("accent"),
                }
            )
        )
        theme.update(
            {
                "layout": data.get("layout") or theme.get("layout", "linktree"),
                "header_mode": data.get("header_mode") or theme.get("header_mode"),
                "header_text": data.get("header_text") or theme.get("header_text"),
                "header_font": data.get("header_font") or theme.get("header_font"),
                "link_font": data.get("link_font") or theme.get("link_font"),
                "bio_font": data.get("bio_font") or theme.get("bio_font"),
                "name_size": data.get("name_size") or theme.get("name_size"),
                "bio_size": data.get("bio_size") or theme.get("bio_size"),
                "wallpaper": data.get("wallpaper") or theme.get("wallpaper"),
                "text_color": data.get("text_color") or theme.get("text_color"),
                "button_style": data.get("button_style") or theme.get("button_style"),
                "button_radius": data.get("button_radius") or theme.get("button_radius"),
                "button_shadow": data.get("button_shadow") or theme.get("button_shadow"),
                "button_bg": data.get("button_bg") or theme.get("button_bg"),
                "button_text": data.get("button_text") or theme.get("button_text"),
                "footer_text": data.get("footer_text") or theme.get("footer_text"),
                "footer_show": _to_bool(data.get("footer_show", theme.get("footer_show", True))),
            }
        )
        self.profile.theme_json = theme
        logo = data.get("logo")
        if logo:
            self.profile.logo = logo
        self.profile.save()

        customer = self.profile.customer
        customer.full_name = data.get("full_name") or customer.full_name
        if data.get("phone"):
            customer.phone = data.get("phone")
        if data.get("email"):
            customer.email = data.get("email")
        customer.save()

        user = customer.user
        if user and data.get("email") and data.get("email") != user.email:
            user.username = data.get("email")
            user.email = data.get("email")
            user.save()

        return self.profile
