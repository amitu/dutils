#!/usr/bin/env python
from django.core.management.base import BaseCommand

from optparse import make_option
import time

from dutils.futures.models import Future

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            "-i", '--include', dest='includes', default=[],
            help='Task type to include.', action="append"
        ),
        make_option(
            "-e", '--exclude', dest='excludes', default=[],
            help='Task type to exclude.', action="append"
        ),
    )
    help = 'Run Pending Actions. Its a never ending process.'

    def handle(self, **options):
        while True:
            start = time.time()
            future = Future.objects.fire_next(
                options["includes"], options["excludes"]
            )
            if future:
                print "Handled a task(%s:%s) in %s seconds. Remaining tasks: %s." % (
                    future.name, future.id, (time.time() - start),
                    Future.objects.overdue().notdone().count()
                )
            else:
                print "Nothing to do, going to sleep."
                time.sleep(5)



