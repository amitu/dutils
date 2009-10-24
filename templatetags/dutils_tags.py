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

