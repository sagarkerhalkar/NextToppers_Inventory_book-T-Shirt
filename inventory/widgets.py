from django import forms
from django.urls import reverse
from django.utils.html import escape, format_html


class AjaxSearchSelect(forms.Widget):
    """Lightweight server-side searchable selector for very large option lists."""

    def __init__(self, endpoint_name, placeholder="Search...", attrs=None):
        super().__init__(attrs)
        self.endpoint_name = endpoint_name
        self.placeholder = placeholder
        self.queryset = None

    def render(self, name, value, attrs=None, renderer=None):
        attrs = self.build_attrs(self.attrs, attrs)
        element_id = attrs.get("id", f"id_{name}")
        selected_label = ""
        if value not in (None, "") and self.queryset is not None:
            try:
                selected = self.queryset.filter(pk=value).first()
                if selected:
                    selected_label = str(selected)
            except (TypeError, ValueError):
                selected_label = ""
        return format_html(
            '<div class="ajax-search-select" data-endpoint="{}">'
            '<input type="search" class="form-control ajax-search-input" id="{}_search" '
            'placeholder="{}" value="{}" autocomplete="off" aria-label="{}">'
            '<input type="hidden" name="{}" id="{}" value="{}">'
            '<div class="ajax-search-results" role="listbox"></div>'
            '<small class="form-text">Type Employee ID, name, mobile, brand or size. Results load from the server.</small>'
            '</div>',
            reverse(self.endpoint_name),
            element_id,
            self.placeholder,
            escape(selected_label),
            self.placeholder,
            name,
            element_id,
            value or "",
        )

    def value_from_datadict(self, data, files, name):
        return data.get(name)
