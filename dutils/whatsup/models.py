# imports # {{{
from django.db import models
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.db.models import Q

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

        def search(self, query):
            return self.public().filter(
                Q(user__username__icontains=query) | Q(text__icontains=query)
            )
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
            ("can_view_status", "Can View Status"),
            ("can_post_status", "Can Post Status"),
            ("can_delete_status", "Can Delete Status"),
            ("can_view_admin", "Can View Admin Page"),
            ("can_update_admin", "Can Change Admin Options"),
        )

    def get_json(self):
        return try_del(
            self.__dict__, "_state", "_user_cache", "deleted_by_id",
            "deleted_on", "is_deleted"
        )

    def soft_delete(self, user):
        self.is_deleted = True
        self.deleted_by = user
        self.deleted_on = datetime.now()
        self.save()
# }}}
