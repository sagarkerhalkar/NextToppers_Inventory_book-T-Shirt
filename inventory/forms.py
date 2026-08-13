from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import BrandingSettings, Book, Employee, TshirtBrand, TshirtPurchase, TshirtStock, User
from .widgets import AjaxSearchSelect


def _past_datetime_field(label):
    return forms.DateTimeField(
        required=False,
        label=label,
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"type": "datetime-local", "max": timezone.localtime().strftime("%Y-%m-%dT%H:%M")},
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
        help_text="Optional. Leave blank to use the current date and time. Future dates are not allowed.",
    )


class StyledFormMixin:
    def _style_fields(self):
        for field in self.fields.values():
            if isinstance(field.widget, AjaxSearchSelect):
                continue
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            if isinstance(field.widget, forms.CheckboxInput):
                css = "form-check-input"
            field.widget.attrs.setdefault("class", css)


class LoginUserCreateForm(StyledFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ["employee_id", "full_name", "mobile_number", "email", "role", "department", "designation", "office_location", "profile_picture"]

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if actor and actor.role == User.Role.ADMIN:
            self.fields["role"].choices = [(User.Role.STAFF, "Data Entry User"), (User.Role.ADMIN, "Admin")]
        self._style_fields()

    def clean_employee_id(self):
        return (self.cleaned_data.get("employee_id") or "").strip().upper()


class LoginUserUpdateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["employee_id", "full_name", "mobile_number", "email", "role", "department", "designation", "office_location", "profile_picture", "is_active"]
        help_texts = {"employee_id": "Correct this ID when it was entered by mistake. It must remain unique."}

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if actor and actor.role == User.Role.ADMIN:
            self.fields["role"].choices = [(User.Role.STAFF, "Data Entry User"), (User.Role.ADMIN, "Admin")]
        self._style_fields()

    def clean_employee_id(self):
        return (self.cleaned_data.get("employee_id") or "").strip().upper()


EmployeeCreateForm = LoginUserCreateForm
EmployeeUpdateForm = LoginUserUpdateForm


class EmployeeRecordForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "employee_id", "full_name", "mobile_number", "email", "department", "designation",
            "joining_date", "office_location", "profile_picture", "default_tshirt_size",
            "tshirt_entitlement_start_date", "tshirt_entitlement_end_date", "is_active", "notes",
        ]
        widgets = {
            "joining_date": forms.DateInput(attrs={"type": "date"}),
            "tshirt_entitlement_start_date": forms.DateInput(attrs={"type": "date"}),
            "tshirt_entitlement_end_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "tshirt_entitlement_start_date": "T-shirt Entitlement Start Date",
            "tshirt_entitlement_end_date": "T-shirt Entitlement End Date",
        }
        help_texts = {
            "employee_id": "This ID can be corrected later when it was entered by mistake.",
            "mobile_number": "Optional. When entered, use +91 followed by the 10-digit Indian mobile number.",
            "tshirt_entitlement_start_date": "Optional Admin setting. Leave both entitlement dates blank to use the normal rolling previous 12 months.",
            "tshirt_entitlement_end_date": "Optional Admin setting. Enter both dates to use a fixed employee-specific period.",
        }

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not actor or actor.role not in {User.Role.ADMIN, User.Role.SUPER_ADMIN}:
            self.fields.pop("tshirt_entitlement_start_date", None)
            self.fields.pop("tshirt_entitlement_end_date", None)
        self._style_fields()

    def clean_employee_id(self):
        return (self.cleaned_data.get("employee_id") or "").strip().upper()

    def clean_mobile_number(self):
        return (self.cleaned_data.get("mobile_number") or "").strip() or None

    def clean(self):
        data = super().clean()
        start = data.get("tshirt_entitlement_start_date")
        end = data.get("tshirt_entitlement_end_date")
        if "tshirt_entitlement_start_date" in self.fields and bool(start) != bool(end):
            raise forms.ValidationError("Enter both T-shirt entitlement dates, or leave both blank.")
        if start and end:
            if end < start:
                self.add_error("tshirt_entitlement_end_date", "End date cannot be before the start date.")
            elif (end - start).days > 366:
                self.add_error("tshirt_entitlement_end_date", "The employee entitlement period cannot be longer than 12 months.")
        return data


class AdminPasswordResetForm(StyledFormMixin, forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput, min_length=4)
    confirm_password = forms.CharField(widget=forms.PasswordInput, min_length=4)

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
        fields = [
            "asset_id", "name", "publication_name", "subject", "class_name", "stream_name",
            "isbn", "purchase_date", "bill_number", "bill_photo", "book_photo", "condition",
        ]
        widgets = {
            "purchase_date": forms.DateInput(attrs={"type": "date"}),
            "asset_id": forms.TextInput(attrs={"placeholder": "Example: NTB-0001"}),
        }
        labels = {
            "asset_id": "Book Number / Asset ID",
            "publication_name": "Publication Name",
            "subject": "Subject",
        }
        help_texts = {
            "asset_id": "Use 3–10 letters, numbers, hyphens or underscores. Leave blank during creation for automatic BOOK000001 format. The number can be corrected later.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["asset_id"].required = True
            self.fields["asset_id"].help_text = "Correct the Book Number / Asset ID here when it was entered by mistake. It must remain unique."
        self._style_fields()

    def clean_asset_id(self):
        return (self.cleaned_data.get("asset_id") or "").strip().upper()


class BookAllocationForm(StyledFormMixin, forms.Form):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        widget=AjaxSearchSelect("inventory:employee_autocomplete", "Search Employee ID, name or mobile"),
    )
    allocated_at = _past_datetime_field("Allocation Date & Time")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Employee.objects.filter(is_active=True).order_by("employee_id")
        self.fields["employee"].queryset = queryset
        self.fields["employee"].widget.queryset = queryset
        self._style_fields()


class BookReturnForm(StyledFormMixin, forms.Form):
    return_condition = forms.ChoiceField(choices=Book.Condition.choices)
    return_note = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
    returned_at = _past_datetime_field("Return Date & Time")

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
        queryset = TshirtStock.objects.select_related("brand").filter(brand__is_active=True).order_by("brand__name", "size")
        self.fields["stock"].queryset = queryset
        self.fields["stock"].widget = AjaxSearchSelect("inventory:tshirt_stock_autocomplete", "Search brand, size or available stock")
        self.fields["stock"].widget.queryset = queryset
        self._style_fields()


class FreeTshirtIssueForm(StyledFormMixin, forms.Form):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        widget=AjaxSearchSelect("inventory:employee_autocomplete", "Search Employee ID, name or mobile"),
    )
    stock = forms.ModelChoiceField(
        queryset=TshirtStock.objects.none(),
        widget=AjaxSearchSelect("inventory:tshirt_stock_autocomplete", "Search T-shirt brand or size"),
    )
    quantity = forms.IntegerField(min_value=1, initial=1)
    issued_at = _past_datetime_field("Issue Date & Time")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        employee_queryset = Employee.objects.filter(is_active=True).order_by("employee_id")
        stock_queryset = TshirtStock.objects.select_related("brand").filter(brand__is_active=True).order_by("brand__name", "size")
        self.fields["employee"].queryset = employee_queryset
        self.fields["employee"].widget.queryset = employee_queryset
        self.fields["stock"].queryset = stock_queryset
        self.fields["stock"].widget.queryset = stock_queryset
        self._style_fields()


class PaidTshirtRequestForm(StyledFormMixin, forms.Form):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        widget=AjaxSearchSelect("inventory:employee_autocomplete", "Search Employee ID, name or mobile"),
    )
    stock = forms.ModelChoiceField(
        queryset=TshirtStock.objects.none(),
        widget=AjaxSearchSelect("inventory:tshirt_stock_autocomplete", "Search T-shirt brand or size"),
    )
    quantity = forms.IntegerField(min_value=1, initial=1)
    requested_at = _past_datetime_field("Request / Entry Date & Time")
    payment_amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    payment_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    payment_proof = forms.FileField()
    hr_approval_proof = forms.FileField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        employee_queryset = Employee.objects.filter(is_active=True).order_by("employee_id")
        stock_queryset = TshirtStock.objects.select_related("brand").filter(brand__is_active=True).order_by("brand__name", "size")
        self.fields["employee"].queryset = employee_queryset
        self.fields["employee"].widget.queryset = employee_queryset
        self.fields["stock"].queryset = stock_queryset
        self.fields["stock"].widget.queryset = stock_queryset
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
