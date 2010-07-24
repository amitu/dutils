from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.exceptions import MiddlewareNotUsed

import re

from dutils.beta import views
from dutils.utils import form_handler
from dutils.beta.models import BetaRequest
from dutils.beta import forms

class Middleware(object):
    def __init__(self):
        if not getattr(settings, "DUTILS_BETA", False):
            raise MiddlewareNotUsed
        self.whitelists = [
            re.compile(r) for r in (
                getattr(settings, "DUTILS_BETA_WHITELIST", ["^/static/"])
            )
        ]

    def is_whitelisted(self, path):
        for r in self.whitelists:
            if r.match(path): return True
        return False

    def should_be_blocked(self, request):
        try:
            br = BetaRequest.objects.get(code=request.COOKIES.get("dbeta", ""))
        except BetaRequest.DoesNotExist:
            return True
        request.dbeta = br
        return False

    def process_request(self, request):
        if self.is_whitelisted(request.path):
            request.dbeta = True
            return
        if request.path == "/iwanna/":
            return form_handler(request, forms.CreateRequest)
        if request.path == "/let-me-in/":
            return form_handler(request, forms.LetMeIn)
        if request.path == "/allow/":
            return form_handler(
                request, forms.Allow, template="dbeta/allow.html"
            )
        if self.should_be_blocked(request):
            return render_to_response(
                "dbeta/index.html", context_instance=RequestContext(request)
            )
