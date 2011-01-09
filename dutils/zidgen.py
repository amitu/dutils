from dutils.zutils import ZReplier, query_maker
import bsddb

ZIDGEN_BIND = "tcp://127.0.0.1:7978"
ZIDGEN_DBFILE = "./zidgen.bdb"

class ZIDGenerator(ZReplier):
    def thread_init(self):
        super(ZIDGenerator, self).thread_init()
        self.db = bsddb.hashopen(ZIDGEN_DBFILE)
        if not "id" in self.db:
            self.db["id"] = "0"
        print "ZIDGenerator initialized with %s, initial id: %s." % (
            ZIDGEN_DBFILE, self.db["id"]
        )

    def get_id(self):
        cid = long(self.db["id"])
        cid += 1
        cid = str(cid)
        self.db["id"] = cid
        return cid

    def reply(self, arguments):
        if arguments == "get":
            return self.get_id()
        return super(ZIDGenerator, self).reply(arguments)

query = query_maker(bind=ZIDGEN_BIND)

if __name__ == "__main__":
    ZIDGenerator(ZIDGEN_BIND).loop()
