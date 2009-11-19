import urllib2, urllib, types
from django.utils import simplejson
from django.conf import settings


def urlencode2(d):
    a = []
    for k in d:
        v = d[k]
        if type(v) == types.ListType:
            for x in v:
                a.append(urllib.urlencode({k: x}))
        if type(v) == types.TupleType:
            for x in v:
                a.append(urllib.urlencode({k: x}))
        else:
            a.append(urllib.urlencode({k: v}))
    return "&".join(a)

def make_request(path, data={}):
    #assert type(data) not in (type(u""), type(""))
    KVDS_ROOT = getattr(settings, "KVDS_ROOT", "http://localhost:8001/")
    print "making request", path, urllib.urlencode(data), KVDS_ROOT
    response = simplejson.loads(
        urllib2.urlopen(
            KVDS_ROOT + path + "/", urllib.urlencode(data)
        ).read()
    )
    return response

def kvds_prefix(prefix):
    return make_request("prefix", dict(prefix=prefix))

def kvds(key, value=None):
    if value:
        return make_request("kvds", dict(kv="%s:%s" % (key, value)))
    # value is either None, "", 0, {}, [] etc. 
    if value is "":
        return make_request("kvds", dict(kv="%s:%s" % (key, value)))
    return make_request("kvds", dict(key=key))

def kvds_multi(keys):
    KVDS_ROOT = getattr(settings, "KVDS_ROOT", "http://localhost:8001/")
    q = urlencode2({ 'key':keys })
    response = simplejson.loads(
        urllib2.urlopen(
            KVDS_ROOT + "kvds/", q
        ).read()
    )
    return response

