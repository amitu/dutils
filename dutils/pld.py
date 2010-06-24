# project less django module 
# imports # {{{ 
from django.core.handlers.base import BaseHandler
from django.conf.urls.defaults import *
from django.conf import settings
from django.core.management import ManagementUtility
from django.http import HttpResponse, Http404

import path, sys
sys.path.append(".")
# }}} 

# get_response_or_urlpatterns # {{{ 
def get_response_or_urlpatterns(get_response):
    old_get_reponse = BaseHandler.get_response
    def decorated(self, request):
        try:
            return get_response(request)
        except Http404:
            return old_get_reponse(self, request)
    return decorated
# }}} 

# handle_folder # {{{ 
def handle_folder(request):
    module_to_import = request.path[1:].replace("/", ".")
    if not module_to_import:
        module_to_import = "index"
    print module_to_import
    try:
        mod = __import__(module_to_import)
    except (ImportError, ValueError), e:
        raise Http404(e)
    resp = mod.handle(request)
    if isinstance(resp, basestring): resp = HttpResponse(resp)
    return resp
# }}} 

# handle # {{{ 
def handle(get_response=handle_folder, **params):
    BaseHandler.get_response = get_response_or_urlpatterns(get_response)
    settings.configure(**params)
    ManagementUtility().execute()
# }}} 

# urlpatterns # {{{ 
urlpatterns = patterns('',
    (
        r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': path.path("./static")}
    ),
)
# }}} 

# get_response # {{{ 
def get_params():
    "get debug, ip, port, from command line"
    base_settings = {
        "DEBUG": True, "INSTALLED_APPS": ["dutils"], "APP_DIR": path.path("."),
        "ROOT_URLCONF": "dutils.pld", "TEMPLATE_DIRS": ["templates",],
    }
    try:
        import settings as local_settings
    except ImportError: 
        pass
    else:
        base_settings.update(local_settings.__dict__)
    return base_settings
# }}} 

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.argv.append("rdebug")
    handle(**get_params())
