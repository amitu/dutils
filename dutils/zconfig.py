from optparse import OptionParser
import zmq, threading, bsddb, time

SERVER_BIND = "tcp://0.0.0.0:5559"
CLIENT_BIND = "tcp://localhost:5559"

CONTEXT = zmq.Context()

class ZConfigServer(threading.Thread):

    def __init__(self, shutdown_event, bind, zfile):
        super(ZConfigServer, self).__init__()
        self.bind = bind
        self.daemon = True
        self.db = bsddb.hashopen(zfile)
        self.shutdown_event = shutdown_event

    def run(self):

        socket = CONTEXT.socket(zmq.REP)
        socket.bind("inproc://zconfig_server")
        socket.bind(self.bind)

        print "Server Started on", self.bind

        while True:
            message = socket.recv()

            try:
                if message.startswith("write"):
                    print "write"
                    cmd, key, val = message.split(":")
                    self.db[key] = val
                    self.db.sync()
                    socket.send("written, thanks")
                elif message == "dump":
                    socket.send(str(dict(self.db)))
                elif message == "shutdown": 
                    socket.send("shutting down")
                    socket.close()
                    self.shutdown_event.set()
                    break
                elif message.startswith("read"):
                    print "read"
                    socket.send(self.db.get(message.split(":", 1)[1], "NA"))
                else:
                    socket.send("Joogi")
            except Exception, e:
                print e
                socket.send(e)

    def shutdown(self):

        socket = CONTEXT.socket(zmq.REQ)
        socket.connect("inproc://zconfig_server")

        socket.send("shutdown")
        socket.recv()

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
    shutdown_event = threading.Event()
    zconfig_server = ZConfigServer(shutdown_event, args[0], options.config_file)
    zconfig_server.start()
    try:
        while True:
            time.sleep(1)
            if shutdown_event.isSet(): 
                print "Terminating after remote signal."
                break
    except KeyboardInterrupt:
        print "Terminating gracefully... ", 
        zconfig_server.shutdown()
        zconfig_server.join()
        print "done."

if __name__ == "__main__":
    main()
