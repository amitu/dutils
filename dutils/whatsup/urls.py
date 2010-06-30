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
    url(r"^(?P<status_id>[\d]+)/$", "show_status", name="whatup_show"),
    fhurl(
        r"^post/", "dutils.whatsup.forms.PostStatus",
        template="whatsup/post.html", name="whatsup_post",
        decorator=perm_required("whatsup.can_post_status"),
    ),
    fhurl(
        r"^(?P<status_id>[\d]+)/delete/$", "dutils.whatsup.forms.DeleteStatus",
        template="whatsup/delete.html", name="whatsup_delete_status",
        decorator=perm_required("whatsup.can_delete_status"),
    ),
)

