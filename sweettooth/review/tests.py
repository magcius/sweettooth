
from django.test import TestCase
from django.core.files.base import File, ContentFile, StringIO

from extensions import models
from review.views import get_old_version

from testutils import BasicUserTestCase

class DiffViewTest(BasicUserTestCase, TestCase):
    def test_get_zipfiles(self):
        metadata = {"uuid": "test-metadata@mecheye.net",
                    "name": "Test Metadata"}

        extension = models.Extension.objects.create_from_metadata(metadata, creator=self.user)
        version1 = models.ExtensionVersion.objects.create(extension=extension,
                                                          source=File(ContentFile("doot doo"), name="aa"),
                                                          status=models.STATUS_NEW)

        # This one is broken...
        version2 = models.ExtensionVersion.objects.create(extension=extension,
                                                          source="",
                                                          status=models.STATUS_NEW)

        version3 = models.ExtensionVersion.objects.create(extension=extension,
                                                          source=File(ContentFile("doot doo"), name="bb"),
                                                          status=models.STATUS_NEW)

        self.assertEquals(version1, get_old_version(version3, None))
