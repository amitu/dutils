"""
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
"""

from django.core.exceptions import ImproperlyConfigured

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
        self._set(self.get_full_key(key), value)

    def single(self, key):
        return self.get(key)

    def session(self, sessionid):
        pass

    def kvds(self, *to_get, **to_set):
        pass

    def prefix(self, prefix):
        raise NotImplementedError

    def close(self): pass

def connect(params):
    return Backend(params)

