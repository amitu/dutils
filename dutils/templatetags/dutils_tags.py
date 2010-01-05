# imports # {{{ 
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.encoding import force_unicode
from django.utils.functional import allow_lazy
from django.conf import settings
from django.utils.safestring import mark_safe
from django.core.urlresolvers import get_mod_func
from django.contrib.flatpages.models import FlatPage

import time, urllib2, os, hashlib

from dutils.utils import logger, batch_gen1
from dutils.kvds import utils as kvds_utils
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

# month_number_to_name # {{{ 
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
            "%m": "MMMMMMMMMMMMMMMMMMMMMMMMMMM",
        }
    }[arg][value]
# }}} 

# truncate_chars # {{{ 
@register.filter
def truncate_chars(s, num):
    """
    Template filter to truncate a string to at most num characters respecting 
    word boundaries.
    """
    s = force_unicode(s)
    length = int(num)
    if len(s) > length:
        length = length - 3
        if s[length-1] == ' ' or s[length] == ' ':
            s = s[:length].strip()
        else:
            words = s[:length].split()
            if len(words) > 1:
                del words[-1]
            s = u' '.join(words)
        s += '...'
    return s
truncate_chars = allow_lazy(truncate_chars, unicode)
# }}} 

# truncatechars # {{{ 
def truncatechars(value, arg):
    """
    Truncates a string after a certain number of characters, but respects word 
    boundaries.
    
    Argument: Number of characters to truncate after.
    """
    try:
        length = int(arg)
    except ValueError: # If the argument is not a valid integer.
        return value # Fail silently.
    return truncate_chars(value, length)
truncatechars.is_safe = True
truncatechars = stringfilter(truncatechars)

register.filter(truncatechars)
# }}} 

# user_visible # {{{
@register.filter
def user_visible(value, arg):
    mod_name, choices_name = get_mod_func(arg)
    choices = getattr(__import__(mod_name, {}, {}, ['']), choices_name)
    choices = dict(choices)
    return choices.get(value, value)
# }}}

# clevercss tag # {{{ 
@register.tag(name="clevercss")
def do_clevercss(parser, token):
    nodelist = parser.parse(('endclevercss',))
    parser.delete_first_token()
    return CleverCSSNode(nodelist)

class CleverCSSNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist
    def render(self, context):
        import CleverCSSNode
        output = self.nodelist.render(context)
        return clevercss.convert(output)
# }}} 

# render_flatpage # {{{ 
@register.simple_tag
def render_flatpage(url):
    try:
        return FlatPage.objects.get(url=url).content
    except FlatPage.DoesNotExist: 
        return ""
# }}} 

# kvds_flatpage # {{{ 
@register.simple_tag
def kvds_flatpage(key):
    return kvds_utils.kvds(key=key).get(key, "")
# }}} 

# gravatar # {{{
@register.filter
@stringfilter
def gravatar(value, arg=""):
    default = getattr(settings, "GRAVATAR_DEFAULT_URL", "identicon")
    parts = arg.split(":")
    if len(parts) == 0: parts = ["80", "g", default]
    if parts[0] == "": parts = ["80", "g", default]
    if len(parts) == 1: parts.extend(["g", default])
    if len(parts) == 2: parts.append(default)
    size, rating, default_image = parts
    if not size: size = "80"
    if not rating: rating = "g"
    return "http://www.gravatar.com/avatar/%s.jpg?s=%s&r=%s&d=%s" % (
        hashlib.md5(value.lower()).hexdigest(), size, rating, default_image
    )
# }}}
