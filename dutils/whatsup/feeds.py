from django.contrib.syndication.views import Feed

from dutils.whatsup.models import Status

class LatestStatusFeed(Feed):
    title = "Latest Status"
    link = "/whatsup/"
    description = "Latest status."

    def items(self):
        return Status.objects.public()[:10]

    def item_title(self, item): return item.text
    def item_description(self, item): return ""
    def item_pubdate(self, item): return item.created_on
