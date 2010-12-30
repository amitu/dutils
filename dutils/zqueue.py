from dutils.zutils import ZReplier, query_maker, send_multi, ZNull

ZQUEQUE_BIND = "tcp://127.0.0.1:7575"

class BDBPersistentQueue(object):
    def __init__(self, db, namespace):
        self.db = db
        self.namespace = namespace

    def get(self, key):
        return self.db["%s:%s" % (self.namespace, key)]

    def set(self, key, value):
        self.db["%s:%s" % (self.namespace, key)] = value

class GettersQueue(object):
    def __init__(self, namespace):
        self.namespace

class NamespacedQueue(object):
    def __init__(self, namespace):
        self.namespace = namespace
        self.pq = BDBPersistentQueue(namespace)
        self.gq = GettersQueue(namespace)

class QueueManager(object):
    def __init__(self):
        self.qs = {}

class ZQueue(ZReplier):
    def __init__(self, bind):
        super(ZQueue, self).__init__(bind)
        self.queue_manager = QueueManager()

    def handle_get(self, namespace):
        pass

    def handle_delete(self, namespace, qid):
        pass

    def handle_add(self, namespace, item):
        pass

    def xreply(self, sender, line):
        try:
            namespace, command = line.split(":", 1)
        except ValueError:
            return send_multi(
                self.socket, [sender, ZNull, super(ZQueue, self).reply(line)]
            )
        print namespace, command
        if command == "get":
            self.handle_get(namespace)
        elif command.startswith("delete"):
            self.handle_delete(namespace, command.split(":", 1)[1])
            send_multi(self.socket, [sender, ZNull, "ack"])
        elif command.startswith("add"):
            self.handle_add(namespace, command.split(":", 1)[1])
            send_multi(self.socket, [sender, ZNull, "ack"])

query = query_maker(bind=ZQUEQUE_BIND)

def main():
    ZQueue(bind=ZQUEQUE_BIND).loop()

if __name__ == "__main__":
    main()
