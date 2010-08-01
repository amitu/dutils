import pytyrant
from django.core.exceptions import ImproperlyConfigured
from dutils.kvds_server.backends import Backend

class TyrantBackend(Backend):
    def __init__(self, params):
        if "port" not in params: 
            raise ImproperlyConfigured("Port not specified")
        if "host" not in params: 
            raise ImproperlyConfigured("Host not specified")
        self.params = params
        self.ty = None

    def connect(self):
        self.ty = pytyrant.PyTyrant.open(
            self.params["host"], int(self.params["port"])
        )
        return self

    def _get(self, key):
        if not self.ty: self.connect()
        return self.ty[key]

    def _set(self, key, value):
        if not self.ty: self.connect()
        self.ty[key] = value

    def _remove(self, key):
        if not self.ty: self.connect()
        del self.ty[key]

    def prefix(self, prefix):
        if not self.ty: self.connect()
        return self.ty.prefix_keys(self.get_full_key(prefix))

    def _contains(self, key):
        if not self.ty: self.connect()
        return self.get_full_key(key) in self.ty

def load(params):
    return TyrantBackend(params)
