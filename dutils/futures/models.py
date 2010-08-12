from django.db import models
from django.db.models.query import QuerySet as DjangoQuerySet
from django.utils import simplejson
from django.core.urlresolvers import get_mod_func

from datetime import datetime, timedelta

from dutils import utils

class Future(models.Model):
    due_on = models.DateTimeField(default=datetime.now)
    name = models.CharField(
        max_length=50, help_text="A name to identify tasks of this kind"
    )
    handler = models.CharField(
        max_length=100,
        help_text="Dotted notation to a callable that will handle this task"
    )
    priority = models.IntegerField(
        default=0, help_text="Tasks with higher priority are given preference."
    )
    params = models.TextField(
        blank=True, help_text="Arbitrary data, to be used by caller"
    )
    allowed_time = models.IntegerField(
        default=300, 
        help_text="""
            Number of seconds should this task be allowed to take before it should
            be considered dead
        """
    )

    fire_on = models.DateTimeField(blank=True, null=True) # main field
    issued_on = models.DateTimeField(blank=True, null=True) # a task is allowed 
    finished_on = models.DateTimeField(blank=True, null=True)

    tries = models.IntegerField(default=0)
    max_tries = models.IntegerField(default=1)

    status = models.CharField(
        max_length=20, default="notdone",
        choices=utils.make_choices("notdone, issued, errored, done, cancelled"),
    )

    error_log = models.TextField(blank=True)
    created_on = models.DateTimeField(default=datetime.now)

    objects = utils.QuerySetManager()

    # QuerySet # {{{
    class QuerySet(DjangoQuerySet):

        def done(self): 
            return self.filter(status="done")

        def notdone(self): 
            return self.filter(status="notdone")

        def issued(self):
            return self.filter(status="issued")

        def overdue(self):
            return self.notdone().filter(fire_on__lte=datetime.now())

        def by_oldest(self):
            return self.order_by("-fire_on")

        def by_priority(self):
            return self.order_by("-priority")

        def get_next(self, includes=None, excludes=None):
            # oldest overdue
            # TODO: use some kind of locking mechanism or transaction
            try:
                # TODO: handle includes and excludes
                future = self.overdue().not_issued().by_oldest()[0]
            except IndexError:
                raise Future.DoesNotExist
            future.mark_issued()

        def fire_next(self, includes=None, excludes=None):
            # the core function
            # this shud take care of state management and exception handling
            try:
                future = self.get_next(includes, excludes) # marks it as issued too
            except Future.DoesNotExist:
                return False # false means no tasks found, and looper shud sleep
            try:
                future.fire() # TODO: put it in a thread and wait for timeout
            except Exception, e:
                future.handle_error(e)
            future.mark_done()
            return future # no need to sleep as there may be more work left

        # TODO: handle locking
        def schedule(self, name, handler, due_on, *args, **kw):
            max_tries = kw.pop("max_tries", 1)
            priority = kw.pop("priority", 0)
            allowed_time = kw.pop("allowed_time", 300)
            params = utils.dump_json(args=args, kw=kw)
            return Future.objects.create(
                due_on=due_on, fire_on=due_on, handler=handler,
                priority=priority, allowed_time=allowed_time, name=name,
                max_tries=max_tries, params=params,
            )
    # }}}

    # utility methods # {{{
    @property
    def handler_object(self):
        mod_name, handler_name = get_mod_func(self.handler)
        return getattr(__import__(mod_name, {}, {}, ['']), handler_name)

    @property
    def args(self): 
        return simplejson.loads(self.params)["args"]

    @property
    def kw(self): 
        return simplejson.loads(self.params)["kw"]

    def log(self, msg, save=True):
        self.error_log = "%s: %s\n%s" % (datetime.now(), msg, self.error_log)
        if save: self.save()
        return self

    # TODO: handle locking
    def mark_issued(self):
        self.status = "issued"
        self.issued_on = datetime.now()
        self.log("Issued", save=False)
        self.save()
        return self

    # TODO: handle locking
    def mark_done(self):
        self.status = "done"
        self.finished_on = datetime.now()
        self.log("Done", save=False)
        self.save()
        return self

    # TODO: handle locking
    def handle_error(self, exception):
        self.tries += 1
        if self.tries >= self.max_tries:
            return self.mark_errored(exception) # this ll save self.
        self.status = "notdone"
        self.fire_on = datetime.now() + timedelta(seconds=self.allowed_time)
        return self

    # TODO: handle locking
    def mark_errored(self, exception): 
        self.status = "errored"
        self.finished_on = datetime.now()
        self.log(
            "Errored, giving up. %s" % utils.format_exception(exception), save=False
        )
        self.save()
        return self

    # TODO: handle locking
    def cancel_it(self, reason=""):
        self.status = "cancelled"
        self.finished_on = datetime.now()
        self.log("Cancelled, reason=%s" % reason, save=False)
        self.save()
        return self

    def fire(self):
        self.log("Firing")
        if getattr(self.handler_object, "raw_handler", False):
            self.log("Handler is raw")
            ret = self.handler_object(self)
        ret = self.handler_object(*self.args, **self.kw)
        self.log("Handler done, returned: %s" % ret)
        return ret
    # }}}


