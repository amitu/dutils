#!/usr/bin/env python
from dutils.futures.management.commands import FuturesBaseCommand

class Command(FuturesBaseCommand):
    help = 'Print the status of pending tasks.'

    def handle_qs(self, qs):
        qs.print_status()

