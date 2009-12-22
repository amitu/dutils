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

import pytyrant, os, random, time

from dutils import utils
from dutils.utils import JSONResponse

from dutils.kvds_server.forms import StoreValue
from dutils.kvds_server import utils as ks_utils

ty = sty = None
# }}}

backend = ks_utils.load_backend()

pid = os.getpid()

# single # {{{
def single(request):
    backend.connect()
    return HttpResponse(
        backend.single(request.GET["key"]), mimetype="text/plain"
    )
# }}}

# kvds # {{{
def kvds(request):
    reopen_connections()
    utils.logger.info('kvds called')
    d = {}
    if "key" in request.REQUEST:
        for key in request.REQUEST.getlist("key"):
            key = key.encode('utf-8')
            if not key in ty: continue
            try:
                d[key] = ty[key]
            except IndexError: pass
    if "kv" in request.REQUEST:
        for kv in request.REQUEST.getlist("kv"):
            if not kv: continue
            key, value = kv.split(":", 1)
            key, value = key.encode('utf-8'), value.encode('utf-8')
            # if value is empty, delete the key from datastore
            if value:
                ty[key] = value
            else:
                if key in ty:
                    del ty[key]
            print key, [ord(c) for c in str(value)]
    if "sessionid" in request.REQUEST:
        sessionid = request.REQUEST["sessionid"]
        sessionkey = str("session_%s" % sessionid)
        data = sty[sessionkey]
        session_data = simplejson.loads(data)
        # TODO load user
        d[":session:"] = session_data
    print "+++++++++++++"
    for v in d.values(): 
        print [ord(c) for c in v]
    return HttpResponse(simplejson.dumps(d), mimetype="text/plain")
# }}}

# start_session # {{{
def start_session(request):
    reopen_connections()
    # create a new unique sessionid, store an empty session in the same
    while True:
        sessionid = md5_constructor(
            "%s%s%s" % (random.random(), pid, time.time())
        ).hexdigest()
        if "session_%s" % sessionid in sty:
            print "SESSIONID CLASH", sessionid
            continue
        else: break
    sty["session_%s" % sessionid] = simplejson.dumps({})
    # TODO: set expiry
    return HttpResponse(simplejson.dumps(dict(sessionid=sessionid)))
# }}}

# session # {{{
def session(request):
    reopen_connections()
    print request.path, request.GET, request.POST
    sessionid = request.REQUEST["sessionid"]
    sessionkey = str("session_%s" % sessionid)
    allow_expired = { "true": True }.get(
        request.REQUEST.get("allow_expired"), False
    )
    d = sty[sessionkey]
    session_data = simplejson.loads(d)
    if "kv" in request.REQUEST:
        for kv in request.REQUEST.getlist("kv"):
            if not kv: continue
            key, value = kv.split(":", 1)
            # if value is empty, delete the key from session
            if value:
                session_data[key] = value
            else:
                if key in session_data:
                    del session_data[key]
        sty[sessionkey] = simplejson.dumps(session_data)
    # TODO: check if expiry is set etc  
    # load user data
    if "user_id" in session_data:
        user_data = simplejson.loads(
            ty[str("user_%s" % session_data["user_id"])]
        )
        session_data["user"] = user_data
        # del session_data["user"]["password"] # TODO required?
        perms = user_data.get("perms", "").split(",")
        for group in user_data.get("groups", "").split(","):
            if not group: continue
            key = str("group_%s_perms" % group)
            perms.extend(ty[key].split(","))
        perms = list(set(perms))
        session_data["user_perms"] = perms
    else:
        session_data["user_perms"] = []
    return HttpResponse(simplejson.dumps(session_data))
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
