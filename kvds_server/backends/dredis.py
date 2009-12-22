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

    def connect(self):
        self.ty = redis.Redis(
            host=self.params["host"], port=int(self.params["port"])
        )
        return self

    def _get(self, key):
        key = key.encode("utf-8")
        return self.ty.get(key)

    def _set(self, key, value):
        key = key.encode("utf-8")
        self.ty.set(key, value)

def load(params):
    return RedisBackend(params)
