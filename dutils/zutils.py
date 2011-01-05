import zmq, threading, time, Queue

CONTEXT = zmq.Context()
ZNull = zmq.Message(None)

# multi helpers # {{{
def recv_multi(sock):
    parts = []
    while True:
        parts.append(sock.recv())
        if not sock.getsockopt(zmq.RCVMORE): break
    return parts

def send_multi(sock, parts, reply=None):
    if reply:
        parts[-1] = reply
    for part in parts[:-1]:
        sock.send(part, zmq.SNDMORE)
    sock.send(parts[-1], 0)
# }}}

class NoReply(Exception): pass

# ZPublisher # {{{
class ZPublisher(threading.Thread):
    def __init__(self, bind):
        super(ZPublisher, self).__init__()
        self.daemon = True
        self.bind = bind
        self.q = Queue.Queue()
        self.start()

    def publish(self, msg): self.q.put(msg)
    def shutdown(self): self.publish("ZPublisher.Shutdown")
    def run(self):
        self.socket = CONTEXT.socket(zmq.PUB)
        self.socket.bind(self.bind)
        print "ZPublisher listening on", self.bind
        while True:
            msg = self.q.get()
            if msg == "ZPublisher.Shutdown":
                self.socket.close()
                break
            self.socket.send(msg)
# }}}

# ZSubscriber # {{{
class ZSubscriber(threading.Thread):
    def __init__(self, bind):
        super(ZSubscriber, self).__init__()
        self.daemon = True
        self.bind = bind
        self.start()

    def process(self, msg): pass

    def run(self):
        self.socket = CONTEXT.socket(zmq.SUB)
        self.socket.bind(self.bind)
        while True:
            self.process(self.socket.recv())
# }}}

# ZReplier # {{{
class ZReplier(threading.Thread):

        def __init__(self, bind):
            super(ZReplier, self).__init__()
            self.shutdown_event = threading.Event()
            self.daemon = True
            self.bind = bind
            self.stats = {}
            self.stats["started_on"] = time.asctime()

        def log(self, message):
            print "[%s] %s" % (time.asctime(), message)

        def thread_init(self):
            self.socket = CONTEXT.socket(zmq.XREP)
            try:
                self.socket.bind(self.bind)
            except zmq.ZMQError, e:
                print e, "while binding on", self.bind
                self.shutdown_event.set()
                raise

        def thread_quit(self):
            self.socket.close()

        def reply(self, message):
            if message == "shutdown":
                self.shutdown_event.set()
                self.log("shutdown")
                self.increment_stats_counter("shutdown")
                return "shutting down"
            if message == "stats":
                from django.utils import simplejson
                self.log("stats")
                self.increment_stats_counter("stats")
                return simplejson.dumps(self.stats)
            self.increment_stats_counter("no_reply")
            raise NoReply

        def increment_stats_counter(self, counter_name):
            if counter_name not in self.stats:
                self.stats[counter_name] = 0
            self.stats[counter_name] += 1

        def run(self):
            self.thread_init()

            print self.__class__.__name__, "listening on %s." % self.bind

            xreply_mode = hasattr(self, "xreply")

            while not self.shutdown_event.isSet():
                parts = recv_multi(self.socket)

                self.increment_stats_counter("requests")

                if len(parts) != 3:
                    self.log(
                        "Expected 3 parts, got %s: %s" % (len(parts), parts)
                    )
                    send_multi(self.socket, parts, "BAD MESSAGE")
                    continue

                message = parts[2]

                try:
                    if xreply_mode:
                        self.xreply(parts[0], message)
                    else:
                        send_multi(self.socket, parts, self.reply(message))
                except NoReply:
                    self.log("NoReply for: %s" % message)
                    send_multi(self.socket, parts, "Unknown command.")
                except Exception, e:
                    self.log("Exception %s for: %s" % (e, message))
                    send_multi(self.socket, parts, "exception: %s" % e)

            self.thread_quit()

        def shutdown(self):
            socket = CONTEXT.socket(zmq.REQ)
            socket.connect(self.bind)

            socket.send("shutdown")
            recv_multi(socket)
            socket.close()

        def loop(self):
            self.start()
            try:
                while True:
                    self.shutdown_event.wait(1)
                    if self.shutdown_event.isSet():
                        print "Terminating after remote signal."
                        break
            except KeyboardInterrupt:
                print "Terminating gracefully... "
                self.shutdown()
                self.join()
                print "Terminated."
# }}}

def query_maker(socket=None, bind=None):
    if not socket:
        assert bind
        socket = CONTEXT.socket(zmq.REQ)
        #socket = CONTEXT.socket(zmq.XREQ)
        socket.connect(bind)

    def query(cmd):
        #socket.send(ZNull, zmq.SNDMORE)
        socket.send(cmd)
        #socket.recv()
        return socket.recv()

    return query

