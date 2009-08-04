# imports # {{{
import threading, Queue, sys, traceback, time
from django.core.mail import send_mail, mail_admins

import dutils.utils
# }}}

# Worker # {{{
class Worker(threading.Thread):
    def __init__(self, queue, shutdown):
        super(Worker, self).__init__()
        self.queue = queue
        self.setDaemon(True)
        self.start()
        self.shutdown = shutdown

    def run(self):
        import Queue
        while True:
            if self.shutdown.isSet(): return
            try: task = self.queue.get(block=True, timeout=1)
            except Queue.Empty: 
                continue
            print "got task:", task, self.queue.qsize()
            try:
                task.process()
            except Exception, e:
                mail_admins(
                    "Task failed: %s" % str(e), 
                    dutils.utils.formatExceptionInfo(), True
                )
            else:
                self.queue.task_done()
            print self.queue.qsize()
# }}}

# tasks # {{{
# EmailTask # {{{
class EmailTask: 
    def __init__(self, *args, **kw):
        self.args = args
        self.kw = kw
    def process(self):
        from dutils import utils
        utils._send_html_mail(*self.args, **self.kw)
# }}}
# }}}

# Messenger # {{{
class Messenger:
    # __init__ # {{{
    def __init__(self):
        self.queue = Queue.Queue(0) # infinite size queue
        self.shutdown = threading.Event()
        self.worker = Worker(self.queue, self.shutdown)
    # }}}
    # send_html_mail # {{{
    def send_html_mail(self, *args, **kw):
        print "send_html_mail called"
        self.queue.put(EmailTask(*args, **kw))
    # }}}
    def join(self):
        print "Messenger.join: Cleaning up Messenger"
        self.queue.join()
        print "Messenger.join: queue empty"
        self.shutdown.set()
        self.worker.join()
        print "Messenger.join: worker done"
# }}}

messenger = Messenger()

import atexit
atexit.register(messenger.join)
