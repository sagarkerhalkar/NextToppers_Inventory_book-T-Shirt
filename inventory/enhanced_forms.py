from django import forms

from .forms import StyledFormMixin
from .models import TshirtBrand, TshirtStock, User


class EmployeeRecipientForm(StyledFormMixin, forms.ModelForm):
    """Create an inventory recipient who does not need application login access."""

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
        self.fields["is_active"].help_text = "Keep active so this employee can receive Books and T-shirts. Login is not enabled."
        self._style_fields()

    def save(self, commit=True):
        employee = super().save(commit=False)
        employee.role = User.Role.STAFF
        employee.set_unusable_password()
        employee.must_change_password = False
        if commit:
            employee.save()
            self.save_m2m()
        return employee


class TshirtBrandForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = TshirtBrand
        fields = ["name", "free_quantity_rolling_12_months", "is_active"]
        labels = {"free_quantity_rolling_12_months": "Free quantity per employee in rolling 12 months"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()

    def save(self, commit=True):
        brand = super().save(commit=commit)
        if commit:
            for size, _label in User.TshirtSize.choices:
                TshirtStock.objects.get_or_create(brand=brand, size=size)
        return brand


class TshirtStockThresholdForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = TshirtStock
        fields = ["low_stock_threshold"]
        labels = {"low_stock_threshold": "Low-stock alert quantity"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()
