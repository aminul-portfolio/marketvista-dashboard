from django import template

register = template.Library()

@register.simple_tag
def pagination_range(current_page, total_pages, delta=2):
    """
    Returns a list like:
    [1, None, 4, 5, 6, None, 20]
    Where None means '...'
    """
    left = max(current_page - delta, 1)
    right = min(current_page + delta, total_pages)

    range_pages = []
    if left > 1:
        range_pages.append(1)
        if left > 2:
            range_pages.append(None)  # Ellipsis

    for i in range(left, right + 1):
        range_pages.append(i)

    if right < total_pages:
        if right < total_pages - 1:
            range_pages.append(None)  # Ellipsis
        range_pages.append(total_pages)

    return range_pages
