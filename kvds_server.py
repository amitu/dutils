from django.http import HttpResponse
from django.utils import simplejson
from django.utils.hashcompat import md5_constructor
from django.conf import settings

import pytyrant, os, random, time

import dutils as utils

ty = sty = None

TYRANT_HOST = getattr(settings, "TYRANT_HOST", "localhost")
TYRANT_PORT = getattr(settings, "TYRANT_PORT", 1978)

def reopen_connections():
    global ty, sty
    ty = pytyrant.PyTyrant.open(TYRANT_HOST, TYRANT_PORT)
    sty = pytyrant.PyTyrant.open(TYRANT_HOST, TYRANT_PORT)

pid = os.getpid()

def kvds(request):
    reopen_connections()
    utils.logger.info('kvds called')
    d = {}
    if "key" in request.REQUEST:
        for key in request.REQUEST.getlist("key"):
            key = key.encode('utf-8')
            if not key in ty: continue
            d[key] = ty[key]
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
    return HttpResponse(simplejson.dumps(d))

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

def prefix(request):
    print "prefix"
    reopen_connections()
    prefix = request.REQUEST['prefix']
    prefix_keys = []
    prefixed_keys = ty.prefix_keys(str(prefix))
    return HttpResponse(simplejson.dumps(prefixed_keys))

from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^start-session/$', start_session),
    (r'^kvds/$', kvds),
    (r'^session/$', session),
    (r'^prefix/$', prefix),
)
