from optparse import OptionParser
from zutils import ZReplier, query_maker
import bsddb, os

ZCONFIG_LOCATION = os.environ.get("ZCONFIG_LOCATION", "tcp://127.0.0.1:5559")
#{{{#}}}
class ZConfigServer(ZReplier):

    def __init__(self, bind, zfile):
        super(ZConfigServer, self).__init__(bind)

        self.db = bsddb.hashopen(zfile)

    def reply(self, message):
        if message.startswith("write"):
            print "write",
            cmd, key, val = message.split(":", 2)
            print key
            self.db[key] = val
            self.db.sync()
            return "written, thanks"
        elif message.startswith("read"):
            print "read",
            key = message.split(":", 1)[1]
            print key
            data = "NA"
            if key in self.db: data = self.db[key]
            return data
        elif message == "dump":
            print "dump"
            return str(dict(self.db))
        else:
            print "joogi:", message
            return "Joogi"

query = query_maker(bind=ZCONFIG_LOCATION)

def main():
    parser = OptionParser()
    parser.add_option(
        "-c", "--config", dest="config_file",
        help="Location of configuration file", default="./zconfig.bdb"
    )
    (options, args) = parser.parse_args()

    if not args: args = (ZCONFIG_LOCATION,)

    zconfig_server = ZConfigServer(args[0], options.config_file)
    zconfig_server.loop()

if __name__ == "__main__":
    main()
