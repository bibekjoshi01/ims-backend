from django import forms
from django.contrib.auth import get_user_model

from tenants.models import Tenant
from tenants.validators import RESERVED_SUBDOMAINS, subdomain_validator

User = get_user_model()

INPUT_CLASS = (
    "mt-1 block w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 "
    "text-white shadow-sm outline-none transition placeholder:text-slate-500 "
    "focus:border-indigo-400 focus:ring-4 focus:ring-indigo-500/20"
)
CHECKBOX_CLASS = (
    "h-4 w-4 rounded border-slate-500 bg-slate-900 text-indigo-400 focus:ring-indigo-500"
)
TEXTAREA_CLASS = INPUT_CLASS


class TailwindFormMixin:
    def _apply_tailwind(self):
        for field in self.fields.values():
            widget = field.widget

            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = CHECKBOX_CLASS
            elif isinstance(widget, forms.Textarea):
                widget.attrs["class"] = TEXTAREA_CLASS
                widget.attrs.setdefault("rows", 4)
            else:
                widget.attrs["class"] = INPUT_CLASS


class TenantForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ["name", "subdomain", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Acme Health"}),
            "subdomain": forms.TextInput(attrs={"placeholder": "acme"}),
            "is_active": forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_tailwind()
        self.fields["name"].label = "Client name"
        self.fields["subdomain"].label = "Subdomain"
        self.fields["is_active"].label = "Client active"
        if self.instance and self.instance.pk:
            self.fields[
                "subdomain"
            ].help_text = "Changing this updates the client subdomain and primary domain."

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_subdomain(self):
        value = self.cleaned_data["subdomain"].strip().lower()

        if value in RESERVED_SUBDOMAINS:
            raise forms.ValidationError("This subdomain is reserved.")

        subdomain_validator(value)
        return value


class TenantUserForm(TailwindFormMixin, forms.ModelForm):
    password = forms.CharField(
        required=False,
        strip=False,
        widget=forms.PasswordInput(
            attrs={"placeholder": "Leave blank to keep the current password"}
        ),
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_no",
            "is_staff",
            "is_superuser",
            "is_active",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "jane.doe"}),
            "email": forms.EmailInput(attrs={"placeholder": "jane@example.com"}),
            "first_name": forms.TextInput(attrs={"placeholder": "Jane"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Doe"}),
            "phone_no": forms.TextInput(attrs={"placeholder": "+977 98xxxxxxx"}),
            "is_staff": forms.CheckboxInput(),
            "is_superuser": forms.CheckboxInput(),
            "is_active": forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_tailwind()
        self.fields["username"].label = "Username"
        self.fields["email"].label = "Email"
        self.fields["first_name"].label = "First name"
        self.fields["last_name"].label = "Last name"
        self.fields["phone_no"].label = "Phone number"
        self.fields["is_staff"].label = "Can access client staff tools"
        self.fields["is_superuser"].label = "Full access"
        self.fields["is_active"].label = "Account active"
        self.fields["password"].widget.attrs["class"] = INPUT_CLASS
        self.fields["password"].widget.attrs["autocomplete"] = "new-password"
        self.fields["password"].label = "Password"
        self.fields["password"].required = not bool(self.instance and self.instance.pk)
        if not self.instance or not self.instance.pk:
            self.fields["is_staff"].initial = True
            self.fields["is_active"].initial = True

    def clean_username(self):
        return self.cleaned_data["username"].strip()

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("is_superuser"):
            cleaned_data["is_staff"] = True

        return cleaned_data

    def save(self, commit=True):
        password = self.cleaned_data.get("password")
        user = super().save(commit=False)

        if password:
            user.set_password(password)
        elif not user.pk and not password:
            raise forms.ValidationError({"password": "Password is required for new users."})

        if commit:
            user.save()
            self.save_m2m()

        return user
