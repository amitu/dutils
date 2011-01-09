from dutils.zutils import ZReplier, query_maker, process_command
from dutils.zidgen import query as zid_query
import bsddb
import json as msgpack

ZUMS_BIND = "tcp://127.0.0.1:7979"

# Store interfaces # {{{
class Store(object): pass
class SessionStore(Store):
    def start_session(self): raise NotImplemented
    def get_session(self, sid): raise NotImplemented
    def save_session(self, sid, **kw): raise NotImplemented
class UserStore(Store): pass
# }}}

# BDBSessionStore # {{{
class BDBSessionStore(SessionStore):
    def __init__(self, db_file="./sessions.bdb"):
        self.db_file = db_file
        self.db = bsddb.hashopen(db_file)

    def start_session(self):
        session = {}
        sid = zid_query("get")
        session["sessionid"] = sid
        self.db[sid] = msgpack.dumps(session)
        return sid

    def get_session(self, sid):
        return self.db[sid]

    def save_session(self, sid, **kw):
        kw.pop("sessionid", None) # ignore sessionid, it can not be changed
        session = msgpack.loads(self.db[sid])
        session.update(kw)
        session = msgpack.dumps(session)
        self.db[sid] = session
        return session
# }}}

class BDBUserStore(UserStore): pass
class DjangoUserStore(SessionStore): pass

class ZUMSServer(ZReplier):
    def __init__(self, bind, session_store_cls, user_store_cls):
        super(ZUMSServer, self).__init__(bind)
        self.session_store_cls = session_store_cls
        self.user_store_cls = user_store_cls

    def thread_init(self):
        super(ZUMSServer, self).thread_init()
        self.session_store = self.session_store_cls()
        self.user_store = self.user_store_cls()

    def reply(self, line):
        arguments = process_command(line)
        print arguments
        if arguments == "start_session":
            return self.session_store.start_session()
        if len(arguments) == 2 and arguments[0] == "get_session":
            return self.session_store.get_session(arguments[1])
        if len(arguments) == 3 and arguments[0] == "save_session":
            return self.session_store.save_session(arguments[1], **arguments[2])
        return super(ZUMSServer, self).reply(line)

query = query_maker(bind=ZUMS_BIND)

if __name__ == "__main__":
    ZUMSServer(ZUMS_BIND, BDBSessionStore, BDBUserStore).loop()
