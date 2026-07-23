from django.core.paginator import Paginator

ALLOWED_PAGE_SIZES = (20, 30)
DEFAULT_PAGE_SIZE = 20


def selected_page_size(request, parameter="page_size"):
    try:
        value = int(request.GET.get(parameter, DEFAULT_PAGE_SIZE))
    except (TypeError, ValueError):
        return DEFAULT_PAGE_SIZE
    return value if value in ALLOWED_PAGE_SIZES else DEFAULT_PAGE_SIZE


def paginate_queryset(request, queryset, *, page_parameter="page", size_parameter="page_size"):
    page_size = selected_page_size(request, size_parameter)
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(request.GET.get(page_parameter))

    query = request.GET.copy()
    query.pop(page_parameter, None)
    query_string = query.urlencode()

    return {
        "page_obj": page_obj,
        "page_size": page_size,
        "page_parameter": page_parameter,
        "size_parameter": size_parameter,
        "page_query": query_string,
    }
