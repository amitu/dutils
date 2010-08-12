from django.db import models
from django.db.models.query import QuerySet as DjangoQuerySet
from django.utils import simplejson
from django.core.urlresolvers import get_mod_func

from datetime import datetime, timedelta
from copy import deepcopy

from dutils import utils

class Future(models.Model):
    due_on = models.DateTimeField(default=datetime.now)
    name = models.CharField(
        max_length=50, help_text="A name to identify tasks of this kind."
    )
    handler = models.CharField(
        max_length=100,
        help_text="Dotted notation to a callable that will handle this task."
    )
    priority = models.IntegerField(
        default=0, help_text="Tasks with higher priority are given preference."
    )
    params = models.TextField(
        blank=True, help_text="Arbitrary data, to be used by caller."
    )
    allowed_time = models.IntegerField(
        default=300, 
        help_text="""

            Number of seconds should this task be allowed to take before it should
            be considered dead.

        """
    )

    fire_on = models.DateTimeField( # main field
        blank=True, null=True, help_text="""

            A task can fail, and multiple retries might be allowed. In case of
            failure, tasks are fired again, and this is the time when the task
            will be actually fired next. It may be later than the due_on above.

        """

    )

    issued_on = models.DateTimeField(
        blank=True, null=True, help_text="""

            A task can take time to run exectute. And there could be multiple
            task servers. In case a task is being run by one task server, we do
            not want to start another instance of task. We also dont want to
            wait for a task indefinitely. For this we need to record when a
            task was issued and thus started on one of the task servers. 

        """
    )

    finished_on = models.DateTimeField(
        blank=True, null=True, help_text="""

            This is when the task "ended". This could be on successful
            completion, on error, or if its cancelled. The actual status is
            stored in status field below.

        """
    )

    tries = models.IntegerField(default=0)
    max_tries = models.IntegerField(default=1)

    status = models.CharField(
        max_length=20, default="notdone",
        choices=utils.make_choices("notdone, issued, errored, done, cancelled"),
    )

    error_log = models.TextField(blank=True)
    created_on = models.DateTimeField(default=datetime.now)

    objects = utils.QuerySetManager()

    def __unicode__(self): 
        return "%(name)s(%(id)s) - %(fire_on)s (%(status)s)" % self.__dict__

    # QuerySet # {{{
    class QuerySet(DjangoQuerySet):

        def done(self): 
            return self.filter(status="done")

        def notdone(self): 
            return self.filter(status="notdone")

        def issued(self):
            return self.filter(status="issued")

        def errored(self):
            return self.filter(status="errored")

        def cancelled(self):
            return self.filter(status="cancelled")

        def overdue(self):
            return self.notdone().filter(fire_on__lte=datetime.now())

        def by_oldest(self):
            return self.order_by("-fire_on")

        def by_priority(self):
            return self.order_by("-priority")

        def with_includes_excludes(self, includes=None, excludes=None):
            return self # TODO

        def copy(self): return deepcopy(self)

        def print_status(self):
            print "Number of tasks:", self.count()
            print "Number of done tasks:", self.copy().done().count()
            print "Number of notdone tasks:", self.copy().notdone().count()
            print "Number of issued tasks:", self.copy().issued().count()
            print "Number of overdue tasks:", self.copy().overdue().count()
            print "Number of errored tasks:", self.copy().errored().count()
            print "Number of cancelled tasks:", self.copy().cancelled().count()

        def get_next(self):
            # oldest overdue
            # TODO: use some kind of locking mechanism or transaction
            try:
                future = self.overdue().notdone().by_oldest()[0]
            except IndexError:
                raise Future.DoesNotExist
            future.mark_issued()
            return future

        def fire_next(self):
            # the core function
            # this shud take care of state management and exception handling
            try:
                future = self.get_next() # marks it as issued too
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
        return dict(
            [
                (str(k), v)
                for k, v in simplejson.loads(self.params)["kw"].items()
            ]
        )

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


