
import os.path

from django.test import TestCase
from extensions.models import Extension, ExtensionVersion

testdata_dir = os.path.join(os.path.dirname(__file__), 'testdata')

def get_test_zipfile(filename):
    return open(os.path.join(testdata_dir, filename), 'rb')

class SimpleTest(TestCase):
    def test_simple_metadata(self):
        metadata = {"name": "Test Metadata",
                    "description": "Simple test metadata",
                    "url": "http://test-metadata.gnome.org"}
        extension, version = ExtensionVersion.from_zipfile(metadata)
        self.assertEquals(extension.name, "Test Metadata")
        self.assertEquals(extension.description, "Simple test metadata")
        self.assertEquals(extension.url, "http://test-metadata.gnome.org")

    def test_empty_metadata(self):
        metadata = {}
        extension, version = ExtensionVersion.from_metadata_json(metadata)

    def test_simple_zipdata_extract(self):
        extension, version = ExtensionVersion.from_zipfile(get_test_zipfile('simple-extension.zip')
        self.assertEquals(extension.name, "Test Extension")
