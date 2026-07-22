from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import TshirtBrand, User


class StyledFormMixin:
    def style(self):
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "form-check-input" if isinstance(field.widget, forms.CheckboxInput)
                else "form-select" if isinstance(field.widget, forms.Select)
                else "form-control",
            )


class EmployeeRecipientForm(StyledFormMixin, forms.ModelForm):
    """Creates an employee inventory record without granting login access."""

    class Meta:
        model = User
        fields = [
            "employee_id", "full_name", "mobile_number", "email", "department",
            "designation", "joining_date", "office_location", "profile_picture",
            "default_tshirt_size", "is_active",
        ]
        widgets = {"joining_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_active"].initial = True
        self.style()

    def save(self, commit=True):
        employee = super().save(commit=False)
        employee.role = User.Role.STAFF
        employee.set_unusable_password()
        if commit:
            employee.save()
            self.save_m2m()
        return employee


class EnableLoginForm(StyledFormMixin, forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput, min_length=10)
    confirm_password = forms.CharField(widget=forms.PasswordInput, min_length=10)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style()

    def clean(self):
        data = super().clean()
        password = data.get("new_password")
        if password != data.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match.")
        if password:
            try:
                validate_password(password)
            except ValidationError as exc:
                self.add_error("new_password", exc)
        return data


class TshirtBrandForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = TshirtBrand
        fields = ["name", "free_quantity_rolling_12_months", "is_active"]
        labels = {
            "free_quantity_rolling_12_months": "Free quantity per employee in rolling 12 months",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style()
