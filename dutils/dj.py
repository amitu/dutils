from django.http import HttpResponse, Http404, HttpResponseRedirect

from django.contrib.auth.models import User

from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from django.views.generic.simple import direct_to_template
from django.contrib.auth.decorators import login_required
