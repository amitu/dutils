"""
kvds server

this file provides views and urls for kvds server, that exposes a key value
database service over variety of key value data stores. 

for now it only supports tokyo tyrant.

to use this, add the following:

    (r'', include('dutils.kvds_server')),

to your urls.py to activate and use this server.

kvds server does not come with any built-in authentication, so you may not want
to expose this to web facing sites, and use it internally only.

please add the following settings:
    TYRANT_HOST: host where tyrant server is running
    TYRANT_PORT: port on which tyrant server is running

"""
# imports # {{{
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.utils.hashcompat import md5_constructor
from django.conf import settings

from dutils import utils
from dutils.utils import JSONResponse

from dutils.kvds_server.forms import StoreValue
from dutils.kvds_server import utils as ks_utils
# }}}

backend = ks_utils.load_backend()

# single # {{{
def single(request):
    return HttpResponse(
        backend.connect().single(request.GET["key"]), mimetype="text/plain"
    )
# }}}

# kvds # {{{
def kvds(request):
    to_set = {}
    for kv in request.REQUEST.getlist("kv"):
        if not kv: continue
        key, value = kv.split(":", 1)
        to_set[str(key)] = value
    return JSONResponse(
        backend.connect().kvds(
            request.REQUEST.get("sessionid"),
            *request.REQUEST.getlist("key"), **to_set
        )
    )
# }}}

# start_session # {{{
def start_session(request):
    backend.connect()
    # create a new unique sessionid, store an empty session in the same
    while True:
        sessionid = utils.uuid()
        if "session_%s" % sessionid in backend:
            print "SESSIONID CLASH", sessionid
            continue
        else: break
    backend.set("session_%s" % sessionid, simplejson.dumps({}))
    return JSONResponse(dict(sessionid=sessionid))
# }}}

# session # {{{
def session(request):
    print request.path, request.GET, request.POST
    to_set = {}
    for kv in request.REQUEST.getlist("kv"):
        if not kv: continue
        key, value = kv.split(":", 1)
        to_set[str(key)] = value
    return JSONResponse(
        backend.connect().session(
            request.REQUEST["sessionid"],
            allow_expired = { "true": True }.get(
                request.REQUEST.get("allow_expired"), False
            ), **to_set
        )
    )
# }}}

# prefix # {{{
def prefix(request):
    return JSONResponse(backend.connect().prefix(request.REQUEST['prefix']))
# }}} 

# index # {{{ 
def index(request):
    backend.connect()
    if request.method == "POST":
        form = StoreValue(request.POST)
        if form.is_valid():
            return HttpResponseRedirect(form.save(backend))
    else:
        initials = {}
        if "key" in request.GET:
            initials = { 
                "key": request.GET["key"],
                "value": backend.get(request.GET["key"])
            }
        form = StoreValue(initial=initials)
    return render_to_response(
        "kvds_index.html", { "form": form }, 
        context_instance=RequestContext(request)
    )
# }}} 
