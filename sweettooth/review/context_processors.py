
from extensions.models import ExtensionVersion, STATUS_LOCKED

def n_unreviewed_extensions(request):
    if not request.user.has_perm("review.can-review-extensions"):
        return dict()

    unreviewed = ExtensionVersion.objects.filter(status=STATUS_LOCKED)
    return dict(n_unreviewed_extensions=unreviewed.count())
