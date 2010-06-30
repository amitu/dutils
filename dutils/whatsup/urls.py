# imports # {{{
from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

from dutils.utils import fhurl

#from dutils.whatsup.feeds import feeds
from dutils.whatsup.views import perm_required
# }}}

urlpatterns = patterns('dutils.whatsup.views',
    url(r"^$", "index", name="whatsup_index"),
    fhurl(
        r"^post/", "dutils.whatsup.forms.PostStatus",
        template="whatsup/post.html", name="whatsup_post",
        decorator=perm_required("can_post_whatsup_status"),
    ),
    url(r"^/(?P<status_id>[\d]+)/$", "show_status", name="whatup_show"),
    url(
        r"^/(?P<status_id>[\d]+)/delete/$",
        "delete_status", name="whatsup_delete"
    ),
)

