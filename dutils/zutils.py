import zmq, threading, time

CONTEXT = zmq.Context()

class ZReplier(threading.Thread):

        def __init__(self, bind):
            super(ZReplier, self).__init__()
            self.shutdown_event = threading.Event()
            self.daemon = True
            self.bind = bind

        def run(self):

            socket = CONTEXT.socket(zmq.REP)
            socket.bind(self.bind)
            socket.bind("inproc://%s" % self.__class__.__name__)

            print self.__class__.__name__, "listening on", self.bind

            while True:
                message = socket.recv()

                if message == "shutdown":
                    socket.send("shutting down")
                    socket.close()
                    self.shutdown_event.set()
                    break

                try:
                    socket.send(self.reply(message))
                except Exception, e:
                    socket.send("exception: %s" % e)

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
