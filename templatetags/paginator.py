# got it from: http://www.djangosnippets.org/snippets/73/
from django import template
import cgi, urllib

register = template.Library()

import dutils

@register.inclusion_tag('paginator.html', takes_context=True)
def paginator(context, adjacent_pages=2):
    """
    To be used in conjunction with the object_list generic view.

    Adds pagination context variables for use in displaying first, adjacent
    and last page links in addition to those created by the object_list
    generic view.
    """
    page_numbers = [
        n 
        for n in range(
            context['page'] - adjacent_pages, 
            context['page'] + adjacent_pages + 1
        ) 
        if n > 0 and n <= context['pages']
    ]
    path = dutils.get_url_with_params(
        context["request"], 
        context.get("paginator_path_override"), without="page"
    )

    return {
        'hits': context['hits'],
        'results_per_page': context['results_per_page'],
        'page': context['page'],
        'pages': context['pages'],
        'page_numbers': page_numbers,
        'next': context['next'],
        'previous': context['previous'],
        'has_next': context['has_next'],
        'has_previous': context['has_previous'],
        'show_first': 1 not in page_numbers,
        'show_last': context['pages'] not in page_numbers,
        'path': path,
    }

