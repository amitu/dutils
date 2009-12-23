""" # Documentation # {{{ 
Backend Base Class
==================

KVDS server talks to various data stores through the API defined in Backend.
Each backend should create a module, module name can be specified as dotted
string, which will be imported by dutils.kvds_server.views.

Each backend is required to have a connect() top level module method, that
will take dbstring as only parameter. connect() must either raise
ImproperlyConfigured error, if parameters passed to it are wrong. If things
are fine, it should return an instance of class derived from
dutils.kvds_server.backends.Backend.

dutils.kvds_server.views expect the backend class to have the following
methods: .kvds(), .single(), .sesssion() and .prefix().
dutils.kvds_server.backends.Backend comes with one implementation of these
methods, expecting each backend to provide .get() and .set() methods. In
certain scenarious, the algorithm used by the default parameters and
multiple cals to .get()/.set() may be inefficeient and it may be desirable
to overwrite one or more of the .kvds()/.single()/.session()/.prefix()
methods.
""" # }}} 

from django.core.exceptions import ImproperlyConfigured
from django.utils import simplejson

class Backend(object):
    def __init__(self, params):
        raise NotImplementedError

    def connect(self): 
        raise NotImplementedError

    def get_full_key(self, key):
        if not "bucket" in self.params:
            return key.encode("utf-8")
        return ("%s.%s" % (self.params["bucket"], key)).encode("utf-8")

    def _get(self, key):
        raise NotImplementedError

    def get(self, key):
        return self._get(self.get_full_key(key))

    def _set(self, key, value):
        raise NotImplementedError

    def set(self, key, value):
        self._set(self.get_full_key(key), value.encode("utf-8"))

    def _remove(self, key):
        raise NotImplementedError

    def remove(self, key):
        self._remove(self.get_full_key(key))

    def single(self, key):
        return self.get(key)

    # session # {{{
    def session(self, sessionid, allow_expired=True, **to_set):
        sessionkey = "session_%s" % sessionid
        d = self.get(sessionkey)
        session_data = simplejson.loads(d)
        if to_set:
            for key, value in to_set.items():
                # if value is empty, delete the key from session
                if value:
                    session_data[key] = value
                else:
                    if key in session_data:
                        del session_data[key]
            self.set(sessionkey, simplejson.dumps(session_data))
        # TODO: check if expiry is set etc.
        # load user data
        if "user_id" in session_data:
            user_data = simplejson.loads(
                self.get("user_%s" % session_data["user_id"])
            )
            session_data["user"] = user_data
            # del session_data["user"]["password"] # TODO required?
            perms = user_data.get("perms", "").split(",")
            for group in user_data.get("groups", "").split(","):
                if not group: continue
                key = "group_%s_perms" % group
                perms.extend(self.get(key).split(","))
            perms = list(set(perms))
            if perms:
                session_data["user_perms"] = perms
        return session_data
    # }}}

    def kvds(self, sessionid=None, *to_get, **to_set):
        d = {}
        for key in to_get:
            try:
                d[key] = self.get(key)
            except IndexError: pass
        if to_set:
            for key, value in to_set.items():
                # if value is empty, delete the key from datastore
                if value:
                    self.set(key, value)
                else:
                    try:
                        self.remove(key)
                    except KeyError: pass
        if sessionid:
            sessionkey = str("session_%s" % sessionid)
            data = self.get(sessionkey)
            session_data = simplejson.loads(data)
            # TODO load user
            d[":session:"] = session_data
        return d

    def prefix(self, prefix):
        raise NotImplementedError

    def close(self): pass

    def __contains__(self, item):
        raise NotImplementedError

def connect(params):
    return Backend(params)

