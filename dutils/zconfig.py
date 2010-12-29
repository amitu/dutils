# imports # {{{
from optparse import OptionParser
from zutils import ZReplier, query_maker, CONTEXT
import bsddb, os, zmq
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
        PUBLISHER_BIND = self.db[BIND_KEY] if BIND_KEY in self.db else DEFAULT_BIND
        self.publisher_port.bind(PUBLISHER_BIND)
        print "ZConfigServer publishing on %s." % PUBLISHER_BIND

    def thread_init(self):
        super(ZConfigServer, self).thread_init()
        self.db = bsddb.hashopen(self.zfile)
        print "Loaded %s with %s records." % (self.zfile, len(self.db))
        self.create_publisher()

    def reply(self, message):
        if message.startswith("write"):
            print "write:",
            cmd, key, val = message.split(":", 2)
            print key
            self.db[key] = val
            self.db.sync()
            self.publisher_port.send("%s:%s" % (key, val))
            return "written, thanks"
        elif message.startswith("read"):
            print "read:",
            key = message.split(":", 1)[1]
            print key
            data = "NA"
            if key in self.db: data = self.db[key]
            return data
        elif message == "dump":
            from django.utils import simplejson
            print "dump"
            return simplejson.dumps(dict(self.db))
        else:
            print "joogi:", message
            return "Joogi"

    def thread_quit(self):
        super(ZConfigServer, self).thread_quit()
        self.publisher_port.close()
# }}}

query = query_maker(bind=ZCONFIG_LOCATION)

def main():
    parser = OptionParser()
    parser.add_option(
        "-c", "--config", dest="config_file",
        help="Location of configuration file", default="./zconfig.bdb"
    )
    (options, args) = parser.parse_args()

    ZConfigServer(
        args[0] if args else ZCONFIG_LOCATION, options.config_file
    ).loop()

if __name__ == "__main__":
    main()
