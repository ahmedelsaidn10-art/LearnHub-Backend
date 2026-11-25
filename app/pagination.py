PAGE_SIZE = 6


def parse_page(value):
    """Read a positive page number from the request query string."""
    if value is None or value == "":
        return 1

    try:
        page = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("page must be a positive whole number.") from error

    if page < 1:
        raise ValueError("page must be a positive whole number.")
    return page


def page_data(page, total_items):
    """Build consistent pagination details for API responses."""
    total_pages = (total_items + PAGE_SIZE - 1) // PAGE_SIZE
    return {
        "page": page,
        "perPage": PAGE_SIZE,
        "totalItems": total_items,
        "totalPages": total_pages,
        "hasNext": page < total_pages,
        "hasPrevious": page > 1,
    }
