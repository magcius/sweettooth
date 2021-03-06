
from django.core import mail
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test import TestCase

from extensions.models import Extension, ExtensionVersion, STATUS_ACTIVE
from errorreports import models

from testutils import BasicUserTestCase

class SubmitErrorReportTestCase(BasicUserTestCase, TestCase):
    def test_email_sent(self):
        metadata = {"uuid": "test-metadata@mecheye.net",
                    "name": "Test Metadata",
                    "description": "Simple test metadata",
                    "url": "http://test-metadata.gnome.org"}

        extension = Extension.objects.create_from_metadata(metadata, creator=self.user)
        version = ExtensionVersion(extension=extension, status=STATUS_ACTIVE)
        version.parse_metadata_json(metadata)
        version.save()

        comment = "YOUR EXTENSION SUCKS IT BROKE"

        self.client.post(reverse('errorreports.views.report_error',
                                 kwargs=dict(pk=extension.pk)),
                         dict(comment=comment), follow=True)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(comment, mail.outbox[0].body)
