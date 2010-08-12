#!/usr/bin/env python
from dutils.futures.management.commands import FuturesBaseCommand
import time

class Command(FuturesBaseCommand):
    help = 'Run Pending Actions. Its a never ending process.'

    def handle_qs(self, qs):
        while True:
            start = time.time()
            future = qs.fire_next()
            if future:
                print "Handled %s in %s seconds. Remaining tasks: %s." % (
                    future, (time.time() - start), qs.overdue().notdone().count()
                )
            else:
                print "Nothing to do, going to sleep."
                time.sleep(5)

