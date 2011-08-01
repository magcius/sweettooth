
import json
import os.path

from django.test import TestCase
from extensions.models import Extension, ExtensionVersion

testdata_dir = os.path.join(os.path.dirname(__file__), 'testdata')

def get_test_zipfile(testname):
    return open(os.path.join(testdata_dir, testname, testname + ".zip"), 'rb')

class UploadTest(TestCase):
    def test_simple_metadata(self):
        metadata = {"name": "Test Metadata",
                    "description": "Simple test metadata",
                    "url": "http://test-metadata.gnome.org"}
        extension, version = ExtensionVersion.from_metadata_json(metadata)
        self.assertEquals(extension.name, "Test Metadata")
        self.assertEquals(extension.description, "Simple test metadata")
        self.assertEquals(extension.url, "http://test-metadata.gnome.org")

    def test_simple_zipdata_data(self):
        extension, version = ExtensionVersion.from_zipfile(get_test_zipfile('SimpleExtension'))
        self.assertEquals(extension.name, "Test Extension")
        self.assertEquals(extension.description, "Simple test metadata")
        self.assertEquals(extension.url, "http://test-metadata.gnome.org")

    def test_extra_metadata(self):
        extension, version = ExtensionVersion.from_zipfile(get_test_zipfile('ExtraMetadata'))
        extra = json.loads(version.extra_json_fields)
        self.assertEquals(extra["extra"], "This is some good data")
        self.assertTrue("description" not in extra)
        self.assertTrue("url" not in extra)
