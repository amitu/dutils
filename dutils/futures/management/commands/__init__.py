from django.core.management.base import BaseCommand

from optparse import make_option

from dutils.futures.models import Future

class FuturesBaseCommand(BaseCommand):
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

    def handle(self, **options):
        qs = Future.objects.with_includes_excludes(
            options["includes"], options["excludes"]
        )
        self.handle_qs(qs)
