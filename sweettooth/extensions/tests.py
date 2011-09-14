
import json
import os.path

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from extensions import models

testdata_dir = os.path.join(os.path.dirname(__file__), 'testdata')

def get_test_zipfile(testname):
    return open(os.path.join(testdata_dir, testname, testname + ".zip"), 'rb')

class UploadTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testing', 'a@a.aa', 'jjj')

    def test_simple_metadata(self):
        metadata = {"name": "Test Metadata",
                    "description": "Simple test metadata",
                    "url": "http://test-metadata.gnome.org"}

        extension = models.Extension(creator=self.user)
        version = models.ExtensionVersion()
        version.extension = extension
        version.parse_metadata_json(metadata)

        self.assertEquals(extension.name, "Test Metadata")
        self.assertEquals(extension.description, "Simple test metadata")
        self.assertEquals(extension.url, "http://test-metadata.gnome.org")

    def test_simple_zipdata_data(self):
        extension = models.Extension(creator=self.user)
        version = models.ExtensionVersion()
        version.extension = extension

        with get_test_zipfile('SimpleExtension') as f:
            metadata = models.parse_zipfile_metadata(f)
        version.parse_metadata_json(metadata)

        self.assertEquals(extension.uuid, "test-extension@gnome.org")
        self.assertEquals(extension.name, "Test Extension")
        self.assertEquals(extension.description, "Simple test metadata")
        self.assertEquals(extension.url, "http://test-metadata.gnome.org")

    def test_upload_parsing(self):
        client = Client()
        client.login(username='testing', password='jjj')

        with get_test_zipfile('SimpleExtension') as f:
            response = client.post(reverse('extensions-upload-file'),
                                   dict(source=f), follow=True)

        extension = models.Extension.objects.get(uuid="test-extension@gnome.org")
        version = extension.versions.order_by("-version")[0]

        url = reverse('extensions-version-detail', kwargs=dict(pk=version.pk,
                                                               ext_pk=extension.pk,
                                                               slug=extension.slug))
        self.assertRedirects(response, url)

        self.assertEquals(extension.creator, self.user)
        self.assertEquals(extension.name, "Test Extension")
        self.assertEquals(extension.description, "Simple test metadata")
        self.assertEquals(extension.url, "http://test-metadata.gnome.org")

    def test_extra_metadata(self):
        extension = models.Extension(creator=self.user)
        version = models.ExtensionVersion()
        version.extension = extension

        with get_test_zipfile('ExtraMetadata') as f:
            metadata = models.parse_zipfile_metadata(f)
        version.parse_metadata_json(metadata)

        extra = json.loads(version.extra_json_fields)
        self.assertEquals(extension.uuid, "test-extension-2@gnome.org")
        self.assertEquals(extra["extra"], "This is some good data")
        self.assertTrue("description" not in extra)
        self.assertTrue("url" not in extra)

class ExtensionVersionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testing', 'a@a.aa', 'jjj')

    def test_single_version(self):
        metadata = {"name": "Test Metadata",
                    "uuid": "test-1@gnome.org",
                    "description": "Simple test metadata",
                    "url": "http://test-metadata.gnome.org"}

        extension = models.Extension(creator=self.user)
        version = models.ExtensionVersion()
        version.extension = extension
        version.parse_metadata_json(metadata)

        version.status = models.STATUS_ACTIVE
        version.save()

        self.assertEquals(version.version, 1)
        self.assertEquals(extension.latest_version, version)

    def test_multiple_versions(self):
        metadata = {"name": "Test Metadata 2",
                    "uuid": "test-2@gnome.org",
                    "description": "Simple test metadata",
                    "url": "http://test-metadata.gnome.org"}

        extension = models.Extension(creator=self.user)

        v1 = models.ExtensionVersion()
        v1.extension = extension
        v1.status = models.STATUS_ACTIVE
        v1.parse_metadata_json(metadata)
        v1.save()
        self.assertEquals(v1.version, 1)

        v2 = models.ExtensionVersion()
        v2.extension = extension
        v2.status = models.STATUS_ACTIVE
        v2.parse_metadata_json(metadata)
        v2.save()
        self.assertEquals(v2.version, 2)

        self.assertEquals(list(extension.visible_versions.order_by('version')), [v1, v2])
        self.assertEquals(extension.latest_version, v2)

    def test_unpublished_version(self):
        metadata = {"name": "Test Metadata 3",
                    "uuid": "test-3@gnome.org",
                    "description": "Simple test metadata",
                    "url": "http://test-metadata.gnome.org"}

        extension = models.Extension(creator=self.user)

        v1 = models.ExtensionVersion()
        v1.extension = extension
        v1.parse_metadata_json(metadata)
        v1.status = models.STATUS_ACTIVE
        v1.save()
        self.assertEquals(v1.version, 1)

        v2 = models.ExtensionVersion()
        v2.extension = extension
        v2.status = models.STATUS_NEW
        v2.parse_metadata_json(metadata)
        v2.save()
        self.assertEquals(v2.version, 2)

        self.assertEquals(list(extension.visible_versions.order_by('version')), [v1])
        self.assertEquals(extension.latest_version, v1)

        v3 = models.ExtensionVersion()
        v3.extension = extension
        v3.status = models.STATUS_ACTIVE
        v3.parse_metadata_json(metadata)
        v3.save()
        self.assertEquals(v3.version, 3)

        self.assertEquals(list(extension.visible_versions.order_by('version')), [v1, v3])
        self.assertEquals(extension.latest_version, v3)

    def test_shell_versions_simple(self):
        metadata = {"name": "Test Metadata 4",
                    "uuid": "test-4@gnome.org",
                    "description": "Simple test metadata",
                    "url": "http://test-metadata.gnome.org",
                    "shell-version": ["3.0.0", "3.0.1", "3.0.2"]}

        extension = models.Extension(creator=self.user)

        version = models.ExtensionVersion()
        version.extension = extension
        version.status = models.STATUS_ACTIVE
        version.parse_metadata_json(metadata)

        version.save()
        shell_versions = sorted([sv.version_string for sv in version.shell_versions.all()])
        self.assertEquals(shell_versions, ["3.0.0", "3.0.1", "3.0.2"])

    def test_shell_versions_stable(self):
        metadata = {"name": "Test Metadata 5",
                    "uuid": "test-5@gnome.org",
                    "description": "Simple test metadata",
                    "url": "http://test-metadata.gnome.org",
                    "shell-version": ["3.0", "3.2"]}

        extension = models.Extension(creator=self.user)

        version = models.ExtensionVersion()
        version.extension = extension
        version.status = models.STATUS_ACTIVE
        version.parse_metadata_json(metadata)

        version.save()
        shell_versions = sorted([sv.version_string for sv in version.shell_versions.all()])
        self.assertEquals(shell_versions, ["3.0", "3.2"])

class ShellVersionTest(TestCase):
    def test_shell_version_parsing_basic(self):
        get_version = models.ShellVersion.objects.get_for_version_string

        version = get_version("3.0.0")
        self.assertEquals(version.major, 3)
        self.assertEquals(version.minor, 0)
        self.assertEquals(version.point, 0)

        version = get_version("3.2")
        self.assertEquals(version.major, 3)
        self.assertEquals(version.minor, 2)
        self.assertEquals(version.point, -1)

        with self.assertRaises(models.InvalidShellVersion):
            version = get_version("3.1")
