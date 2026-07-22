from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import BrandingSettings, Book, TshirtAllocation, TshirtBrand, TshirtPurchase, TshirtStock, User


class StyledFormMixin:
    def _style_fields(self):
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            if isinstance(field.widget, forms.CheckboxInput):
                css = "form-check-input"
            field.widget.attrs.setdefault("class", css)


class EmployeeCreateForm(StyledFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ["employee_id", "full_name", "mobile_number", "email", "role", "department", "designation", "joining_date", "office_location", "profile_picture", "default_tshirt_size"]
        widgets = {"joining_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if actor and actor.role == User.Role.ADMIN:
            self.fields["role"].choices = [(User.Role.STAFF, "Staff"), (User.Role.ADMIN, "Admin")]
        self._style_fields()


class EmployeeRecordForm(StyledFormMixin, forms.ModelForm):
    """Creates an employee used only for inventory allocation/history, without login access."""

    class Meta:
        model = User
        fields = ["employee_id", "full_name", "mobile_number", "email", "department", "designation", "joining_date", "office_location", "profile_picture", "default_tshirt_size"]
        widgets = {"joining_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()

    def save(self, commit=True):
        employee = super().save(commit=False)
        employee.role = User.Role.STAFF
        employee.is_staff = False
        employee.must_change_password = False
        employee.set_unusable_password()
        if commit:
            employee.save()
            self.save_m2m()
        return employee


class EmployeeUpdateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["full_name", "mobile_number", "email", "role", "department", "designation", "joining_date", "office_location", "profile_picture", "default_tshirt_size", "is_active"]
        widgets = {"joining_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if actor and actor.role == User.Role.ADMIN:
            self.fields["role"].choices = [(User.Role.STAFF, "Staff"), (User.Role.ADMIN, "Admin")]
        self._style_fields()


class AdminPasswordResetForm(StyledFormMixin, forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput, min_length=10)
    confirm_password = forms.CharField(widget=forms.PasswordInput, min_length=10)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()

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


class BookForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Book
        fields = ["name", "class_name", "stream_name", "isbn", "purchase_date", "bill_number", "bill_photo", "book_photo", "condition"]
        widgets = {"purchase_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class BookAllocationForm(StyledFormMixin, forms.Form):
    employee = forms.ModelChoiceField(queryset=User.objects.none())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["employee"].queryset = User.objects.filter(is_active=True).order_by("employee_id")
        self._style_fields()


class BookReturnForm(StyledFormMixin, forms.Form):
    return_condition = forms.ChoiceField(choices=Book.Condition.choices)
    return_note = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class TshirtBrandForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = TshirtBrand
        fields = ["name", "free_quantity_rolling_12_months", "is_active"]
        labels = {"free_quantity_rolling_12_months": "Free quantity per employee in rolling 12 months"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class TshirtPurchaseForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = TshirtPurchase
        fields = ["stock", "purchase_date", "vendor", "bill_number", "bill_photo", "quantity", "total_cost"]
        widgets = {"purchase_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class FreeTshirtIssueForm(StyledFormMixin, forms.Form):
    employee = forms.ModelChoiceField(queryset=User.objects.none())
    stock = forms.ModelChoiceField(queryset=TshirtStock.objects.none())
    quantity = forms.IntegerField(min_value=1, initial=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["employee"].queryset = User.objects.filter(is_active=True).order_by("employee_id")
        self.fields["stock"].queryset = TshirtStock.objects.select_related("brand").filter(brand__is_active=True).order_by("brand__name", "size")
        self._style_fields()


class PaidTshirtRequestForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = TshirtAllocation
        fields = ["employee", "stock", "quantity", "payment_amount", "payment_date", "payment_proof", "hr_approval_proof"]
        widgets = {"payment_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["employee"].queryset = User.objects.filter(is_active=True).order_by("employee_id")
        self.fields["stock"].queryset = TshirtStock.objects.select_related("brand").filter(brand__is_active=True).order_by("brand__name", "size")
        self._style_fields()


class RejectionForm(StyledFormMixin, forms.Form):
    rejection_reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class BrandingForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = BrandingSettings
        fields = ["organization_name", "app_logo", "login_background", "home_image", "organization_picture"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()

    def clean(self):
        data = super().clean()
        for name in ["app_logo", "login_background", "home_image", "organization_picture"]:
            image = data.get(name)
            if image and getattr(image, "size", 0) > 8 * 1024 * 1024:
                self.add_error(name, "Image size must not exceed 8 MB.")
        return data
