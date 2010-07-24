from django.db import models
from django.contrib.auth.models import User

from datetime import datetime

class BetaRequestManager(models.Manager):
    def create_beta_request(self, email):
        br = BetaRequest.objects.get_or_create(email=email)[0]
        # TODO: send mail
        return br

class BetaRequest(models.Model):
    email = models.EmailField(unique=True)
    code = models.CharField(max_length=32)

    created_on = models.DateTimeField(default=datetime.now)

    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, blank=True, null=True)
    approved_on = models.DateTimeField(blank=True, null=True)

    accessed = models.BooleanField(default=False)
    first_access_on = models.DateTimeField(blank=True, null=True)

    objects = BetaRequestManager()

    def __unicode__(self):
        return "%s: %s" % (
            self.email, (self.approved if self.code else "pending")
        )

    def approve(self, user):
        assert not self.approved
        self.approved_by = user
        self.approved_by = datetime.now()
        self.save()
        # TODO: send mail

    def set_accessed_if_required(self):
        if self.accessed: return
        self.accessed = True
        self.first_access_on = datetime.now()
        self.save()
