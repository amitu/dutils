from django import forms
from django.core.urlresolvers import reverse

from dutils import utils

from dutils.whatsup.models import Status

class PostStatus(utils.RequestForm):
    text = forms.CharField(widget=forms.Textarea)

    def save(self):
        self.obj = Status.objects.create(
            text=self.cleaned_data["text"], user=self.request.user
        )
        return reverse("whatsup_index")
