import redis
from django.core.exceptions import ImproperlyConfigured
from dutils.kvds_server.backends import Backend

class RedisBackend(Backend):
    def __init__(self, params):
        if "port" not in params: 
            raise ImproperlyConfigured("Port not specified")
        if "host" not in params: 
            raise ImproperlyConfigured("Host not specified")
        self.params = params
        self.ty = None

    def connect(self):
        self.ty = redis.Redis(
            host=self.params["host"], port=int(self.params["port"])
        )
        return self

    def _get(self, key):
        if not self.ty: self.connect()
        return self.ty.get(key)

    def _set(self, key, value):
        if not self.ty: self.connect()
        self.ty.set(key, value)

    def prefix(self, prefix):
        if not self.ty: self.connect()
        return self.ty.keys("%s*" % self.get_full_key(prefix))

    def _contains(self, key):
        if not self.ty: self.connect()
        return self.ty.exists(self.get_full_key(key))

def load(params):
    return RedisBackend(params)
