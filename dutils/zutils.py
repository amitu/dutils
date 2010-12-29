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

class ZReplier(threading.Thread):

        def __init__(self, bind):
            super(ZReplier, self).__init__()
            self.shutdown_event = threading.Event()
            self.daemon = True
            self.bind = bind

        def thread_init(self):
            self.socket = CONTEXT.socket(zmq.XREP)
            self.socket.bind(self.bind)

        def thread_quit(self):
            self.socket.close()

        def run(self):
            self.thread_init()

            print self.__class__.__name__, "listening on", self.bind

            while True:
                parts = recv_multi(self.socket)

                assert len(parts) == 3

                message = parts[2]

                if message == "shutdown":
                    send_multi(self.socket, parts, "shutting down")
                    self.socket.close()
                    self.shutdown_event.set()
                    break

                try:
                    send_multi(self.socket, parts, self.reply(message))
                except Exception, e:
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

