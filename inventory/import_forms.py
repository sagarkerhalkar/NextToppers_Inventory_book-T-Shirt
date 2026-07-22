from pathlib import Path

from django import forms


class BulkImportForm(forms.Form):
    class ImportType(forms.TextChoices):
        EMPLOYEES = "employees", "Employees"
        BOOKS = "books", "Books"
        TSHIRTS = "tshirts", "T-shirt stock"

    import_type = forms.ChoiceField(choices=ImportType.choices)
    excel_file = forms.FileField(help_text="Upload an .xlsx file. Maximum size: 10 MB.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["import_type"].widget.attrs["class"] = "form-select"
        self.fields["excel_file"].widget.attrs["class"] = "form-control"

    def clean_excel_file(self):
        uploaded = self.cleaned_data["excel_file"]
        if Path(uploaded.name).suffix.lower() != ".xlsx":
            raise forms.ValidationError("Only .xlsx Excel files are supported.")
        if uploaded.size > 10 * 1024 * 1024:
            raise forms.ValidationError("Excel file size must not exceed 10 MB.")
        return uploaded
