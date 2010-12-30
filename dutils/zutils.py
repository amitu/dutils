import zmq, threading, time

CONTEXT = zmq.Context()

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

class NoReply(Exception): pass

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
                print e
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
                    time.sleep(1)
                    if self.shutdown_event.isSet():
                        print "Terminating after remote signal."
                        break
            except KeyboardInterrupt:
                print "Terminating gracefully... "
                self.shutdown()
                self.join()
                print "Terminated."

def query_maker(socket=None, bind=None):
    if not socket:
        assert bind
        socket = CONTEXT.socket(zmq.REQ)
        #socket = CONTEXT.socket(zmq.XREQ)
        socket.connect(bind)

    def query(cmd):
        #socket.send(zmq.Message(None), zmq.SNDMORE)
        socket.send(cmd)
        #socket.recv()
        return socket.recv()

    return query

