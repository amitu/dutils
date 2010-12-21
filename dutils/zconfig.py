from optparse import OptionParser
from zutils import ZReplier, CONTEXT
import zmq, bsddb, os

SERVER_BIND = "tcp://0.0.0.0:5559"
CLIENT_BIND = os.environ.get("ZCONFIG_LOCATION", "tcp://localhost:5559")

class ZConfigServer(ZReplier):

    def __init__(self, bind, zfile):
        super(ZConfigServer, self).__init__(bind)

        self.db = bsddb.hashopen(zfile)

    def reply(self, message):
        if message.startswith("write"):
            print "write"
            cmd, key, val = message.split(":", 2)
            self.db[key] = val
            self.db.sync()
            return "written, thanks"
        elif message.startswith("read"):
            key = message.split(":", 1)[1]
            data = "NA"
            if key in self.db: self.db[key]
            return data
        elif message == "dump":
            return str(dict(self.db))
        else:
            return "Joogi"

def query(socket, cmd):
    socket.send(cmd)
    return socket.recv()

def query_maker(socket=None, bind=CLIENT_BIND):

    if not socket:
        socket = CONTEXT.socket(zmq.REQ)
        socket.connect(bind)

    def wrapper(cmd):
        return query(socket, cmd)

    return wrapper

def main():
    parser = OptionParser()
    parser.add_option(
        "-c", "--config", dest="config_file",
        help="Location of configuration file", default="./zconfig.bdb"
    )
    (options, args) = parser.parse_args()

    if not args: args = (SERVER_BIND,)

    zconfig_server = ZConfigServer(args[0], options.config_file)
    zconfig_server.loop()

if __name__ == "__main__":
    main()
