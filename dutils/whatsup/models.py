# imports # {{{
from django.db import models
from django.contrib.auth.models import User
from django.db.models.query import QuerySet

from datetime import datetime

from dutils.utils import QuerySetManager, try_del
# }}}

# Status # {{{
class Status(models.Model):
    text = models.TextField()
    user = models.ForeignKey(User, related_name="status_i_created")
    is_deleted = models.BooleanField(default=False)
    deleted_by = models.ForeignKey(
        User, blank=True, null=True, related_name="status_i_deleted"
    )
    deleted_on = models.DateTimeField(blank=True, null=True)

    created_on = models.DateTimeField(default=datetime.now)
    objects = QuerySetManager()

    # QuerySet # {{{
    class QuerySet(QuerySet):
        def public(self):
            return self.filter(is_deleted=False)

        def by_recency(self):
            return self.order_by("-created_on")
    # }}}

    @models.permalink
    def get_absolute_url(self):
        return ("dutils.whatsup.views.show_status", str(self.id))

    @models.permalink
    def get_delete_url(self):
        return ("dutils.whatsup.views.delete_status", str(self.id))

    def __unicode__(self):
        return u"%s: %s" % (self.user, self.text)

    class Meta:
        ordering = ["-created_on"]
        verbose_name_plural = "status"
        get_latest_by = "created_on"
        permissions = (
            ("can_view_whatsup_status", "Can View Whatsup Status"),
            ("can_post_whatsup_status", "Can Post Whatsup Status"),
            ("can_delete_whatsup_status", "Can Delete Whatsup Status"),
            ("can_view_whatsup_admin", "Can View Whatsup Admin Page"),
            ("can_update_whatsup_admin", "Can Change Whatsup Admin Options"),
        )

    def get_json(self): return try_del(self.__dict__, "_state", "_user_cache")
# }}}
