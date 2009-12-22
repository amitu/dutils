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

    def connect(self):
        self.ty = pytyrant.PyTyrant.open(
            self.params["host"], int(self.params["port"])
        )
        return self

    def _get(self, key):
        key = key.encode("utf-8")
        return self.ty[key]

    def _set(self, key, value):
        key = key.encode("utf-8")
        self.ty[key] = value

def load(params):
    return TyrantBackend(params)
