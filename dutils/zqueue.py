from dutils.zutils import ZReplier, query_maker, send_multi, ZNull
import threading, time, Queue

ZQUEQUE_BIND = "tcp://127.0.0.1:7575"
DURATION = 5

# BDBPersistentQueue # {{{
class BDBPersistentQueue(object):
    def __init__(self, db, namespace):
        self.db = db
        self.namespace = namespace
        if not self.has_key("top"): self.set("top", 0)
        if not self.has_key("bottom"): self.set("bottom", 0)
        if not self.has_key("seen"): self.set("seen", 0)

    def get_top(self): return int(self.get("top"))
    def set_top(self, v): self.set("top", str(v))
    def get_bottom(self): return int(self.get("bottom"))
    def set_bottom(self, v): self.set("bottom", str(v))
    def get_seen(self): return int(self.get("seen"))
    def set_seen(self, v): self.set("seen", str(v))

    top = property(get_top, set_top)
    bottom = property(get_bottom, set_bottom)
    seen = property(get_seen, set_seen)

    def has_key(self, key):
        return "%s:%s" % (self.namespace, key) in self.db

    def get(self, key):
        return self.db["%s:%s" % (self.namespace, key)]

    def set(self, key, value):
        self.db["%s:%s" % (self.namespace, key)] = str(value)

    def del_key(self, key):
        del self.db["%s:%s" % (self.namespace, key)]

    def add(self, item):
        next_id = self.top = self.top + 1
        self.set(next_id, item)
        return next_id

    def pop_item(self): pass

    def is_empty(self):
        start, end = self.seen, self.top
        if start == end: return True
        while start <= end:
            if self.has_key(start): return True
        return False

    def delete(self, item_id):
        self.del_key(item_id)
        item_id = int(item_id) + 1
        top = self.top
        if item_id != self.bottom: return
        while item_id <= top and self.has_key(item_id):
            item_id += 1
        self.bottom = item_id
        if self.seen < item_id: self.seen = item_id
# }}}

# GettersQueue # {{{
class GettersQueue(object):
    def __init__(self, namespace):
        self.namespace
        self.q = Queue.Queue()

    def pop_getter(self): return self.q.get()
    def is_empty(self): return self.q.empty()
    def add(self, getter): self.q.put(getter)
# }}}

# NamespacedQueue # {{{
class NamespacedQueue(object):
    def __init__(self, namespace):
        self.namespace = namespace
        self.pq = BDBPersistentQueue(namespace)
        self.gq = GettersQueue(namespace)
# }}}

# DelayedResetter # {{{
class DelayedResetter(threading.Thread):
    def __init__(self, item_id, requester):
        self.item_id = item_id
        self.requester = requester
        self.ignore_it = threading.Event()

    def run(self):
        time.sleep(DURATION)
        if self.ignore_it.isSet(): return
        query("reset:%s" % self.item_id)
# }}}

# Single Threaded QueueManager # {{{
class QueueManager(object):
    def __init__(self, socket):
        self.qs = {}
        self.socket = socket
        self.assigned_items = {}

    def get_q(self, namespace):
        if namespace not in self.qs:
            self.qs[namespace] = NamespacedQueue(namespace)
        return self.qs[namespace]

    def assign_item(self, item_id, item, requester):
        send_multi(self.socket, [requester, ZNull, item_id + ":" + item])
        self.assigned_items[item_id] = DelayedResetter(item_id, requester)

    def assign_next_if_possible(self, q):
        if q.pq.is_empty() or q.gq.is_empty(): return
        item_id, item = q.pq.pop_item()
        requester = q.gq.pop_getter()
        self.assign_item(item_id, item, requester)

    def handle_get(self, namespace, sender):
        q = self.get_q(namespace)
        if q.pq.is_empty():
            q.gq.add(sender)
        else:
            item_id, item = q.pq.pop_item()
            self.assign_item(item_id, item, sender)

    def handle_delete(self, namespace, item_id):
        q = self.get_q(namespace)
        q.pq.delete(item_id)
        self.assigned_items[item_id].ignore_it.set()
        del self.assigned_items[item_id]

    def handle_add(self, namespace, item):
        q = self.get_q(namespace)
        q.pq.add(item)
        self.assign_next_if_possible(q)

    def handle_reset(self, namespace, item_id):
        q = self.get_q(namespace)
        del self.assigned_items[item_id]
        self.assign_next_if_possible(q)
# }}}

# ZQueue # {{{
class ZQueue(ZReplier):
    def __init__(self, bind):
        super(ZQueue, self).__init__(bind)
        self.qm = QueueManager(self.socket)

    def xreply(self, sender, line):
        try:
            namespace, command = line.split(":", 1)
        except ValueError:
            return send_multi(
                self.socket, [sender, ZNull, super(ZQueue, self).reply(line)]
            )
        print namespace, command
        if command == "get":
            self.qm.handle_get(namespace, sender)
        elif command.startswith("delete"):
            self.qm.handle_delete(namespace, command.split(":", 1)[1])
            send_multi(self.socket, [sender, ZNull, "ack"])
        elif command.startswith("add"):
            self.qm.handle_add(namespace, command.split(":", 1)[1])
            send_multi(self.socket, [sender, ZNull, "ack"])
        elif command.startswith("reset"):
            self.qm.handle_reset(namespace, command.split(":", 1)[1])
            send_multi(self.socket, [sender, ZNull, "ack"])
# }}}

query = query_maker(bind=ZQUEQUE_BIND)

def main():
    ZQueue(bind=ZQUEQUE_BIND).loop()

if __name__ == "__main__":
    main()
