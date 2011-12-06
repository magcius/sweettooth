
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from extensions.models import Extension

class LatestExtensionsFeed(Feed):
    title = "Latest extensions in GNOME Shell Extensions"
    link = "/"
    description = "The latest extensions in GNOME Shell Extensions"

    def items(self):
        return Extension.objects.visible().order_by('pk')[-10:]

    def item_title(self, item):
        return item.name

    def item_description(self, item):
        return item.description

    def item_link(self, item):
        return reverse('extensions-detail', kwargs=dict(pk=item.pk,
                                                        slug=item.slug))
