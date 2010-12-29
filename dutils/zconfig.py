# imports # {{{
from optparse import OptionParser
from zutils import ZReplier, query_maker, CONTEXT
import bsddb, os, zmq, time
# }}}

ZCONFIG_LOCATION = os.environ.get("ZCONFIG_LOCATION", "tcp://127.0.0.1:5559")

# ZConfigServer # {{{
class ZConfigServer(ZReplier):

    def __init__(self, bind, zfile):
        super(ZConfigServer, self).__init__(bind)

        self.zfile = zfile

    def create_publisher(self):
        self.publisher_port = CONTEXT.socket(zmq.PUB)
        BIND_KEY = "dutils.zconfig.publisher_port"
        DEFAULT_BIND = "tcp://127.0.0.1:5558"
        if BIND_KEY in self.db:
            PUBLISHER_BIND = self.db[BIND_KEY]
        else:
            PUBLISHER_BIND = DEFAULT_BIND
            self.db[BIND_KEY] = DEFAULT_BIND
            self.db.sync()
        self.publisher_port.bind(PUBLISHER_BIND)
        print "ZConfigServer publishing on %s." % PUBLISHER_BIND

    def thread_init(self):
        super(ZConfigServer, self).thread_init()
        self.db = bsddb.hashopen(self.zfile)
        print "Loaded %s with %s records." % (self.zfile, len(self.db))
        self.create_publisher()

    def reply(self, message):
        if message.startswith("write"):
            print time.asctime(), "write:",
            cmd, key, val = message.split(":", 2)
            print key
            self.db[key] = val
            self.db.sync()
            self.publisher_port.send("%s:%s" % (key, val))
            return "written, thanks"
        elif message.startswith("del"):
            print time.asctime(), "del:",
            key = message.split(":", 1)[1]
            print key
            if key in self.db: 
                del self.db[key]
                self.db.sync()
                return "deleted"
            return "not found"
        elif message.startswith("read"):
            print time.asctime(), "read:",
            key = message.split(":", 1)[1]
            print key
            data = "NA"
            if key in self.db: data = self.db[key]
            return data
        elif message == "dump":
            from django.utils import simplejson
            print time.asctime(), "dump"
            return simplejson.dumps(dict(self.db))
        else:
            print time.asctime(), "joogi:", message
            return "Joogi"

    def thread_quit(self):
        super(ZConfigServer, self).thread_quit()
        self.publisher_port.close()
# }}}

query = query_maker(bind=ZCONFIG_LOCATION)

def printer(key, value):
    print "%s: %s" % (key, value)

def watch(callback=printer):
    socket = CONTEXT.socket(zmq.SUB)
    socket.connect(query("read:dutils.zconfig.publisher_port"))
    socket.setsockopt(zmq.SUBSCRIBE, "")
    while True:
        k, v = socket.recv().split(":", 1)
        callback(k, v)

def main():
    parser = OptionParser()
    parser.add_option(
        "-c", "--config", dest="config_file",
        help="Location of configuration file", default="./zconfig.bdb"
    )
    (options, args) = parser.parse_args()

    if args and args[0] == "read":
        for k in args[1:]:
            print "%s: %s" % (k, query("read:%s" % k))
        return

    if args and args[0] == "del":
        for k in args[1:]:
            print "%s: %s" % (k, query("del:%s" % k))
        return

    if args and args[0] == "dump":
        print query("dump")
        return

    if args and args[0] == "write":
        print query("write:%s:%s" % (args[1], args[2]))
        return

    ZConfigServer(
        args[0] if args else ZCONFIG_LOCATION, options.config_file
    ).loop()

if __name__ == "__main__":
    main()
