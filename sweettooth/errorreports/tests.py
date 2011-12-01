
from django.core import mail
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test import TestCase

from extensions.models import Extension, ExtensionVersion, STATUS_ACTIVE
from errorreports import models

class SubmitErrorReportTestCase(TestCase):
    def setUp(self):
        super(SubmitErrorReportTestCase, self).setUp()
        self.username = 'TestUser1'
        self.email = 'non-existant@non-existant.tld'
        self.password = 'a random password'
        self.user = User.objects.create_user(self.username, self.email, self.password)

        self.client.login(username=self.username, password=self.password)

        self.extension = Extension.objects.create(creator=self.user,
                                                  name="Testing One",
                                                  uuid="testing-one@aa",
                                                  description="AAA",
                                                  url="hey ya")
        self.version = ExtensionVersion.objects.create(extension=self.extension,
                                                       source="",
                                                       status=STATUS_ACTIVE)
        self.extension.save()
        self.version.save()

    def test_no_contact_information(self):
        comment = "No contact information"

        response = self.client.post(reverse('errorreports-report', kwargs=dict(pk=self.extension.pk)),
                                    dict(can_contact=False,
                                         comment=comment), follow=True)

        self.assertEqual(len(mail.outbox), 1)
        error_report = models.ErrorReport.objects.get(comment=comment)
        self.assertEqual(error_report.can_contact, False)

    def test_with_contact_information(self):
        comment = "With contact information"

        self.client.post(reverse('errorreports-report', kwargs=dict(pk=self.extension.pk)),
                         dict(can_contact=True,
                              comment=comment), follow=True)

        self.assertEqual(len(mail.outbox), 1)
        error_report = models.ErrorReport.objects.get(comment=comment)
        self.assertEqual(error_report.can_contact, True)
