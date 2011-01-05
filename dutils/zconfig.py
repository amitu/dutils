# imports # {{{
from optparse import OptionParser
import bsddb, os, zmq
from pprint import pprint
from zutils import ZReplier, query_maker, CONTEXT, ZPublisher
# }}}

ZCONFIG_LOCATION = os.environ.get("ZCONFIG_LOCATION", "tcp://127.0.0.1:5559")

# ZConfigServer # {{{
class ZConfigServer(ZReplier):

    def __init__(self, bind, zfile):
        super(ZConfigServer, self).__init__(bind)

        self.zfile = zfile

    def create_publisher(self):
        BIND_KEY = "dutils.zconfig.publisher_port"
        DEFAULT_BIND = "tcp://127.0.0.1:5558"
        if BIND_KEY in self.db:
            PUBLISHER_BIND = self.db[BIND_KEY]
        else:
            PUBLISHER_BIND = DEFAULT_BIND
            self.db[BIND_KEY] = DEFAULT_BIND
            self.db.sync()
        self.publisher = ZPublisher(PUBLISHER_BIND)
        print "ZConfigServer publishing on %s." % PUBLISHER_BIND

    def thread_init(self):
        super(ZConfigServer, self).thread_init()
        self.db = bsddb.hashopen(self.zfile)
        print "Loaded %s with %s records." % (self.zfile, len(self.db))
        self.create_publisher()

    def reply(self, message):
        if message.startswith("write"):
            cmd, key, val = message.split(":", 2)
            self.log("write: %s" % key)
            self.increment_stats_counter("write")
            self.db[key] = val
            self.db.sync()
            self.publisher.publish("%s:%s" % (key, val))
            return "written, thanks"
        elif message.startswith("del"):
            key = message.split(":", 1)[1]
            self.log("del: %s" % key)
            self.increment_stats_counter("del")
            if key in self.db: 
                del self.db[key]
                self.db.sync()
                return "deleted"
            return "not found"
        elif message.startswith("read"):
            key = message.split(":", 1)[1]
            self.log("read: %s" % key)
            self.increment_stats_counter("read")
            data = "NA"
            if key in self.db: data = self.db[key]
            return data
        elif message == "dump":
            from django.utils import simplejson
            self.log("dump")
            self.increment_stats_counter("dump")
            return simplejson.dumps(dict(self.db))
        return super(ZConfigServer, self).reply(message)

    def thread_quit(self):
        super(ZConfigServer, self).thread_quit()
        self.publisher.shutdown()
# }}}

query = query_maker(bind=ZCONFIG_LOCATION)

NOT_SET = object()

def get(key, default=NOT_SET):
    data = query("read:%s" % key, raw_output=True)
    print data
    if data == "NA" and default != NOT_SET:
        query("write:%s:%s" % (key, default))
        data = default
    assert data != "NA"
    return data


# watch for changes # {{{
def printer(key, value):
    print "%s: %s" % (key, value)

def watch(callback=printer):
    socket = CONTEXT.socket(zmq.SUB)
    socket.connect(query("read:dutils.zconfig.publisher_port"))
    socket.setsockopt(zmq.SUBSCRIBE, "")
    while True:
        k, v = socket.recv().split(":", 1)
        callback(k, v)
# }}}

# command line handling # {{{
def main():
    parser = OptionParser()
    parser.add_option(
        "-c", "--config", dest="config_file",
        help="Location of configuration file", default="./zconfig.bdb"
    )
    (options, args) = parser.parse_args()

    if args and args[0] == "read":
        for k in args[1:]:
            print "%s: %s" % (k, query("read:%s" % k, raw_output=True))
        return

    if args and args[0] == "delete":
        for k in args[1:]:
            print "%s: %s" % (k, query("del:%s" % k))
        return

    if args and args[0] == "dump":
        pprint(query("dump"))
        return

    if args and (args[0] == "list" or args[0] == "ls"):
        d = query("dump")
        keys = d.keys()
        keys.sort()
        f = ""
        if len(args) > 1: f = args[1]
        for k in keys:
            if f not in k: continue
            print "%s: %s" % (k, d[k])
        return

    if args and args[0] == "write":
        print query("write:%s:%s" % (args[1], args[2]))
        return

    if args and args[0] == "watch":
        watch()
        return

    if args and args[0] == "stats":
        for k, v in query("stats").items():
            print "%s: %s" % (k, v)
        return

    if len(args) != 0:
        print "Bad argument passed: %s" % " ".join(args)
        return

    ZConfigServer(
        args[0] if args else ZCONFIG_LOCATION, options.config_file
    ).loop()
# }}}

if __name__ == "__main__":
    main()
