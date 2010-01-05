# imports # {{{ 
from django.conf import settings

import cgi
# }}} 

# parse_dbstring # {{{ 
def parse_dbstring(dbstring):
    try:
        parts = dbstring.split("?", 1)
    except (AttributeError, IndexError): 
        raise ImproperlyConfigured
    return parts[0], dict(cgi.parse_qsl(parts[1]))
# }}} 

# load_backend # {{{ 
def load_backend(
    dbstring=getattr(
        settings, "KVDS_BACKEND", "tyrant?host=localhost&port=1978"
    )
):
    backend, params = parse_dbstring(dbstring)
    print backend, params
    try:
        backend = __import__(
            "dutils.kvds_server.backends." + backend, {}, {}, ['']
        )
    except ImportError, e:
        print e
        backend = __import__(backend, {}, {}, [''])
    return backend.load(params)
# }}} 
