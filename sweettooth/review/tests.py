
from django.test import TestCase
from django.core.files.base import File, ContentFile, StringIO

from extensions import models
from review.views import get_old_version, should_auto_approve, should_auto_reject

from testutils import BasicUserTestCase

class DiffViewTest(BasicUserTestCase, TestCase):
    def test_get_zipfiles(self):
        metadata = {"uuid": "test-metadata@mecheye.net",
                    "name": "Test Metadata"}

        extension = models.Extension.objects.create_from_metadata(metadata, creator=self.user)
        version1 = models.ExtensionVersion.objects.create(extension=extension,
                                                          source=File(ContentFile("doot doo"), name="aa"),
                                                          status=models.STATUS_NEW)
        self.assertEquals(None, get_old_version(version1))

        # This one is broken...
        version2 = models.ExtensionVersion.objects.create(extension=extension,
                                                          source="",
                                                          status=models.STATUS_NEW)
        self.assertEquals(version1, get_old_version(version2))

        version3 = models.ExtensionVersion.objects.create(extension=extension,
                                                          source=File(ContentFile("doot doo"), name="bb"),
                                                          status=models.STATUS_NEW)
        self.assertEquals(version1, get_old_version(version3))

class TestAutoApproveLogic(TestCase):
    def build_changeset(self, added=None, deleted=None, changed=None, unchanged=None):
        return dict(added=added or [],
                    deleted=deleted or [],
                    changed=changed or [],
                    unchanged=unchanged or [])

    def test_auto_approve_logic(self):
        self.assertTrue(should_auto_approve(self.build_changeset()))
        self.assertTrue(should_auto_approve(self.build_changeset(changed=['metadata.json'])))
        self.assertTrue(should_auto_approve(self.build_changeset(changed=['metadata.json', 'po/en_GB.po', 'images/new_fedora.png', 'stylesheet.css'])))
        self.assertTrue(should_auto_approve(self.build_changeset(changed=['stylesheet.css'], added=['po/zn_CH.po'])))

        self.assertFalse(should_auto_approve(self.build_changeset(changed=['extension.js'])))
        self.assertFalse(should_auto_approve(self.build_changeset(changed=['secret_keys.json'])))
        self.assertFalse(should_auto_approve(self.build_changeset(changed=['libbignumber/BigInteger.js'])))
        self.assertFalse(should_auto_approve(self.build_changeset(added=['libbignumber/BigInteger.js'])))

class TestAutoReject(BasicUserTestCase, TestCase):
    def test_shell_version_auto_reject(self):
        metadata = {"name": "Test Metadata 10",
                    "uuid": "test-10@mecheye.net",
                    "description": "Simple test metadata",
                    "url": "http://test-metadata.gnome.org"}

        extension = models.Extension.objects.create_from_metadata(metadata, creator=self.user)
        version1 = models.ExtensionVersion.objects.create(extension=extension, status=models.STATUS_UNREVIEWED)
        version1.parse_metadata_json({'shell-version': ["3.4", "3.2.1"]})

        version2 = models.ExtensionVersion.objects.create(extension=extension, status=models.STATUS_UNREVIEWED)

        version2.parse_metadata_json({'shell-version': ["3.4"]})
        self.assertFalse(should_auto_reject(version1, version2))

        version2.parse_metadata_json({'shell-version': ["3.2.1"]})
        self.assertTrue(should_auto_reject(version1, version2))

        # As this safely covers all of version 1's shell versions,
        # it should be rejected
        version2.parse_metadata_json({'shell-version': ["3.6"]})
        self.assertTrue(should_auto_reject(version1, version2))

    def test_existing_version_auto_reject(self):
        metadata = {"name": "Test Metadata 11",
                    "uuid": "test-11@mecheye.net",
                    "description": "Simple test metadata",
                    "url": "http://test-metadata.gnome.org"}

        extension = models.Extension.objects.create_from_metadata(metadata, creator=self.user)
        version1 = models.ExtensionVersion.objects.create(extension=extension, status=models.STATUS_ACTIVE)
        version1.parse_metadata_json({'shell-version': ["3.4", "3.2.1"]})

        version2 = models.ExtensionVersion.objects.create(extension=extension, status=models.STATUS_UNREVIEWED)
        version2.parse_metadata_json({'shell-version': ["3.4", "3.2.1"]})

        self.assertFalse(should_auto_reject(version1, version2))
