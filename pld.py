# project less django module
from django.core.handlers.base import BaseHandler
from django.conf import settings
from django.core.management import ManagementUtility
from django.http import HttpResponse, Http404

def get_response_or_urlpatterns(get_response):
    old_get_reponse = BaseHandler.get_response
    def decorated(self, request):
        try:
            return get_response(request)
        except Http404:
            return old_get_reponse(self, request)
    return decorated

def handle_folder(request):
    try:
        mod = __import__(request.path.split("/")[1]) # FIXME
    except (ImportError, ValueError), e:
        raise Http404(e)
    resp = mod.handle(request)
    if isinstance(resp, basestring): resp = HttpResponse(resp)
    return resp

def handle(get_response=handle_folder, **params):
    BaseHandler.get_response = get_response_or_urlpatterns(get_response)
    settings.configure(**params)
    ManagementUtility().execute()

def get_params():
    "get debug, ip, port, from command line"
    return { "DEBUG": True }

if __name__ == "__main__":
    handle(**get_params())
