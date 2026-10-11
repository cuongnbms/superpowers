import math


def paginate(items, page, per_page):
    """Return the items shown on a 1-indexed page."""
    start = (page - 1) * per_page
    end = start + per_page + 1
    return items[start:end]


def total_pages(count, per_page):
    return max(1, math.ceil(count / per_page))
