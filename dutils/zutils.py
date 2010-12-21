import zmq, threading, time

CONTEXT = zmq.Context()

class ZReplier(threading.Thread):

        def __init__(self, bind):
            super(ZReplier, self).__init__()
            self.shutdown_event = threading.Event()
            self.daemon = True
            self.bind = bind

        def thread_init(self):
            self.socket = CONTEXT.socket(zmq.REP)
            self.socket.bind(self.bind)
            self.socket.bind("inproc://%s" % self.__class__.__name__)

        def thread_quit(self):
            self.socket.close()

        def run(self):
            self.thread_init()

            print self.__class__.__name__, "listening on", self.bind

            while True:
                message = self.socket.recv()

                if message == "shutdown":
                    self.socket.send("shutting down")
                    self.socket.close()
                    self.shutdown_event.set()
                    break

                try:
                    self.socket.send(self.reply(message))
                except Exception, e:
                    self.socket.send("exception: %s" % e)

            self.thread_quit()

        def shutdown(self):
            socket = CONTEXT.socket(zmq.REQ)
            socket.connect("inproc://%s" % self.__class__.__name__)

            socket.send("shutdown")
            socket.recv()

        def loop(self):
            self.start()
            try:
                while True:
                    time.sleep(1)
                    if self.shutdown_event.isSet():
                        print "Terminating after remote signal"
                        break
            except KeyboardInterrupt:
                print "Terminating gracefully... ",
                self.shutdown()
                self.join()
                print "done."

def query_maker(socket=None, bind=None):
    if not socket:
        assert bind
        socket = CONTEXT.socket(zmq.REQ)
        socket.connect(bind)

    def query(cmd):
        socket.send(cmd)
        return socket.recv()

    return query

