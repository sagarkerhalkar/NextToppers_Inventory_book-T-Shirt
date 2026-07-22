from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("change-temporary-password/", views.change_temporary_password, name="change_temporary_password"),
    path("", views.dashboard, name="dashboard"),
    path("books/", views.book_list, name="book_list"),
    path("books/add/", views.book_create, name="book_create"),
    path("books/<int:pk>/edit/", views.book_edit, name="book_edit"),
    path("books/<int:pk>/allocate/", views.book_allocate_view, name="book_allocate"),
    path("book-allocations/<int:pk>/return/", views.book_return_view, name="book_return"),
    path("books/<int:pk>/delete/", views.book_delete, name="book_delete"),
    path("employees/", views.employee_list, name="employee_list"),
    path("employees/add/", views.employee_create, name="employee_create"),
    path("employees/<int:pk>/edit/", views.employee_edit, name="employee_edit"),
    path("employees/<int:pk>/reset-password/", views.employee_reset_password, name="employee_reset_password"),
    path("tshirts/stock/", views.tshirt_stock_list, name="tshirt_stock_list"),
    path("tshirts/purchases/add/", views.tshirt_purchase_create, name="tshirt_purchase_create"),
    path("tshirts/issue-free/", views.free_tshirt_issue, name="free_tshirt_issue"),
    path("tshirts/request-paid/", views.paid_tshirt_request, name="paid_tshirt_request"),
    path("tshirts/allocations/", views.tshirt_allocation_list, name="tshirt_allocation_list"),
    path("tshirts/allocations/<int:pk>/approve/", views.paid_tshirt_approve, name="paid_tshirt_approve"),
    path("tshirts/allocations/<int:pk>/reject/", views.paid_tshirt_reject, name="paid_tshirt_reject"),
    path("settings/branding/", views.branding_settings, name="branding"),
    path("reports/", views.reports_index, name="reports"),
    path("backups/download/", views.download_database_backup, name="download_database_backup"),
    path("reports/books.xlsx", views.export_books_excel, name="export_books_excel"),
    path("reports/books.pdf", views.export_books_pdf, name="export_books_pdf"),
    path("reports/tshirts.xlsx", views.export_tshirts_excel, name="export_tshirts_excel"),
]
