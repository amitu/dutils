# imports # {{{ 
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.encoding import force_unicode
from django.utils.functional import allow_lazy
from django.conf import settings
from django.utils.safestring import mark_safe

import time, urllib2
import os

from dutils.utils import logger, batch_gen1
# }}}

register = template.Library()

# icontains # {{{
@register.filter
@stringfilter
def icontains(value,arg):
    return arg.lower() in value.lower()
# }}}

# contains # {{{
@register.filter
@stringfilter
def contains(value,arg):
    return arg in value
# }}}

# format_timestamp # {{{
@register.filter
@stringfilter
def format_timestamp(value,arg):
    try:
        local_t = time.localtime(float(value))
        return time.strftime(arg, local_t)
    except:
        return
# }}}

# batch # {{{
@register.filter
def batch(value, arg):
    return list(batch_gen1(value, int(arg)))
# }}}

# month_number_to_name
@register.filter
def month_number_to_name(value, arg="1"):
    return {
        "1": {
            "01": "Jan",
            "02": "Feb",
            "03": "Mar",
            "04": "Apr",
            "05": "May",
            "06": "June",
            "07": "July",
            "08": "Aug",
            "09": "Sept",
            "10": "Oct",
            "11": "Nov",
            "12": "Dec",
        }
    }[arg][value]
# }}} 
