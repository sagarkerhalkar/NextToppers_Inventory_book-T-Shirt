import mimetypes
from pathlib import Path

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404

from .models import Book, TshirtAllocation, TshirtPurchase, User
from .permissions import role_required
from .services import audit


def _document_response(request, field_file, fallback_name):
    if not field_file:
        raise Http404("Document is not available.")
    try:
        handle = field_file.open("rb")
    except (FileNotFoundError, ValueError, OSError) as exc:
        raise Http404("Document file is not available.") from exc
    filename = Path(field_file.name).name or fallback_name
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    as_attachment = request.GET.get("download") == "1"
    response = FileResponse(handle, content_type=content_type, as_attachment=as_attachment, filename=filename)
    if not as_attachment:
        response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def book_document(request, pk, document_type):
    book = get_object_or_404(Book, pk=pk)
    fields = {"photo": book.book_photo, "bill": book.bill_photo}
    labels = {"photo": "Book photo", "bill": "Book bill"}
    if document_type not in fields:
        raise Http404("Unknown Book document.")
    action = "DOWNLOADED" if request.GET.get("download") == "1" else "VIEWED"
    audit(request.user, f"BOOK_DOCUMENT_{action}", book, f"{action.title()} {labels[document_type]} for {book.asset_id}")
    return _document_response(request, fields[document_type], f"{book.asset_id}_{document_type}")


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def paid_tshirt_document(request, pk, document_type):
    allocation = get_object_or_404(TshirtAllocation, pk=pk, issue_type=TshirtAllocation.IssueType.PAID)
    fields = {"payment": allocation.payment_proof, "hr": allocation.hr_approval_proof}
    labels = {"payment": "Payment proof", "hr": "HR approval proof"}
    if document_type not in fields:
        raise Http404("Unknown paid T-shirt document.")
    action = "DOWNLOADED" if request.GET.get("download") == "1" else "VIEWED"
    audit(request.user, f"PAID_TSHIRT_DOCUMENT_{action}", allocation, f"{action.title()} {labels[document_type]} for paid request {allocation.pk}")
    return _document_response(request, fields[document_type], f"paid_request_{allocation.pk}_{document_type}")


@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def tshirt_purchase_document(request, pk):
    purchase = get_object_or_404(TshirtPurchase.objects.select_related("stock", "stock__brand"), pk=pk)
    action = "DOWNLOADED" if request.GET.get("download") == "1" else "VIEWED"
    audit(
        request.user,
        f"TSHIRT_PURCHASE_BILL_{action}",
        purchase,
        f"{action.title()} purchase bill for {purchase.stock.brand.name}/{purchase.stock.size}, purchase {purchase.pk}",
    )
    return _document_response(request, purchase.bill_photo, f"tshirt_purchase_{purchase.pk}_bill")
