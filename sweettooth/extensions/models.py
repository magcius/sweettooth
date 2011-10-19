
import os
try:
    import json
except ImportError:
    import simplejson as json

import uuid
from zipfile import ZipFile, BadZipfile

from django.contrib import auth
from django.db import models
from django.dispatch import Signal

import autoslug
from sorl import thumbnail

(STATUS_NEW, STATUS_LOCKED,
 STATUS_REJECTED, STATUS_INACTIVE,
 STATUS_ACTIVE) = xrange(5)

STATUSES = {
    STATUS_NEW: u"New",
    STATUS_LOCKED: u"Unreviewed",
    STATUS_REJECTED: u"Rejected",
    STATUS_INACTIVE: u"Inactive",
    STATUS_ACTIVE: u"Active",
}

VISIBLE_STATUSES = (STATUS_ACTIVE,)
REJECTED_STATUSES = (STATUS_REJECTED,)
EDITABLE_STATUSES = (STATUS_NEW, STATUS_ACTIVE)
REVIEWED_STATUSES = (STATUS_REJECTED, STATUS_INACTIVE, STATUS_ACTIVE)

class ExtensionManager(models.Manager):
    def visible(self):
        return self.filter(versions__status__in=VISIBLE_STATUSES).distinct()

class Extension(models.Model):
    name = models.CharField(max_length=200)
    uuid = models.CharField(max_length=200, unique=True, db_index=True)
    slug = autoslug.AutoSlugField(populate_from="name")
    creator = models.ForeignKey(auth.models.User, db_index=True)
    description = models.TextField()
    url = models.URLField(verify_exists=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = (
            ("can-modify-data", "Can modify extension data"),
        )

    def make_screenshot_filename(self, filename):
        return os.path.join(self.uuid, filename)

    screenshot = thumbnail.ImageField(upload_to=make_screenshot_filename, blank=True)

    def make_icon_filename(self, filename):
        return os.path.join(self.uuid, "icons/", filename)

    icon = models.ImageField(upload_to=make_icon_filename, blank=True, default="")

    objects = ExtensionManager()

    def __unicode__(self):
        return self.uuid

    @property
    def visible_versions(self):
        return self.versions.filter(status__in=VISIBLE_STATUSES)

    @property
    def latest_version(self):
        qs = self.visible_versions.order_by("-version")
        if qs.exists():
            return qs[0]
        return None

    def user_has_access(self, user):
        if user == self.creator:
            return True
        if user.has_perm('extensions.can-modify-data'):
            return True
        return False

class InvalidShellVersion(Exception):
    pass

class ShellVersionManager(models.Manager):
    def get_for_version_string(self, version_string):
        version = version_string.split('.', 2)
        major, minor = version[:2]
        major, minor = int(major), int(minor)

        if len(version) >= 3:
            # 3.0.1, 3.1.4
            point = int(version[2])
        elif len(version) == 2 and minor % 2 == 0:
            # 3.0, 3.2
            point = -1
        else:
            # Two-digit odd versions are illegal: 3.1, 3.3
            raise InvalidShellVersion()

        obj, created = self.get_or_create(major=major, minor=minor, point=point)
        return obj

class ShellVersion(models.Model):
    major = models.PositiveIntegerField()
    minor = models.PositiveIntegerField()

    # -1 is a flag for the stable release matching
    point = models.IntegerField()

    objects = ShellVersionManager()

    def __unicode__(self):
        return self.version_string

    @property
    def version_string(self):
        if self.point == -1:
            return "%d.%d" % (self.major, self.minor)

        return "%d.%d.%d" % (self.major, self.minor, self.point)

class InvalidExtensionData(Exception):
    pass


def parse_zipfile_metadata(uploaded_file):
    """
    Given a file, extract out the metadata.json, parse, and return it.
    """
    try:
        zipfile = ZipFile(uploaded_file, 'r')
    except BadZipfile:
        raise InvalidExtensionData("Invalid zip file")

    try:
        metadata = json.load(zipfile.open('metadata.json', 'r'))
    except KeyError:
        # no metadata.json in archive, return nothing
        metadata = {}
    except ValueError:
        # invalid JSON file, raise error
        raise InvalidExtensionData("Invalid JSON data")

    zipfile.close()
    return metadata

# uuid max length + suffix max length
filename_max_length = Extension._meta.get_field('uuid').max_length + len(".v000.shell-version.zip")

class ExtensionVersionManager(models.Manager):
    def locked(self):
        return self.filter(status=STATUS_LOCKED)

    def visible(self):
        return self.filter(status__in=VISIBLE_STATUSES)

class ExtensionVersion(models.Model):
    extension = models.ForeignKey(Extension, related_name="versions")
    version = models.IntegerField(default=0)
    extra_json_fields = models.TextField()
    status = models.PositiveIntegerField(choices=STATUSES.items())
    shell_versions = models.ManyToManyField(ShellVersion)

    class Meta:
        unique_together = ('extension', 'version'),

    def __unicode__(self):
        return "Version %d of %s" % (self.version, self.extension)

    def make_filename(self, filename):
        return "%s.v%d.shell-extension.zip" % (self.extension.uuid, self.version)

    source = models.FileField(upload_to=make_filename,
                              max_length=filename_max_length)

    objects = ExtensionVersionManager()

    @property
    def shell_versions_json(self):
        return json.dumps([sv.version_string for sv in self.shell_versions.all()])

    def make_metadata_json(self):
        """
        Return generated contents of metadata.json
        """
        data = json.loads(self.extra_json_fields)
        fields = dict(
            _generated  = "Generated by SweetTooth, do not edit",
            name        = self.extension.name,
            description = self.extension.description,
            url         = self.extension.url,
            uuid        = self.extension.uuid,
        )

        fields['shell-version'] = [sv.version_string for sv in self.shell_versions.all()]

        data.update(fields)
        return data

    def make_metadata_json_string(self):
        return json.dumps(self.make_metadata_json(), sort_keys=True, indent=2)

    def get_zipfile(self, mode):
        return ZipFile(self.source.storage.path(self.source.name), mode)

    def replace_metadata_json(self):
        """
        In the uploaded extension zipfile, edit metadata.json
        to reflect the new contents.
        """

        # We can't easily *replace* files in a zipfile
        # archive. See http://bugs.python.org/issue6818.
        # Just read all the contents from the old zipfile
        # into memory and then emit a new one with the
        # generated metadata.json
        zipfile_in = self.get_zipfile("r")

        filemap = {}
        for info in zipfile_in.infolist():
            if info.filename == "metadata.json":
                continue

            contents = zipfile_in.read(info)
            filemap[info] = contents

        zipfile = self.get_zipfile("w")
        for info, contents in filemap.iteritems():
            zipfile.writestr(info, contents)

        metadata = self.make_metadata_json()
        zipfile.writestr("metadata.json", self.make_metadata_json_string())
        zipfile.close()

    def parse_metadata_json(self, metadata):
        """
        Given the contents of a metadata.json file, fill in the fields
        of the version and associated extension.
        """
        assert self.extension is not None

        # Only parse the standard data for a new extension
        if self.extension.pk is None:
            self.extension.name = metadata.pop('name', "")
            self.extension.description = metadata.pop('description', "")
            self.extension.url = metadata.pop('url', "")
            self.extension.uuid = metadata.pop('uuid', str(uuid.uuid1()))
            self.extension.save()

            # Due to Django ORM magic and stupidity, this is unfortunately necessary
            self.extension = self.extension

        # FIXME: We shouldn't do this, but Django saving requires it.
        if self.status is None:
            self.status = STATUS_NEW

        self.extra_json_fields = json.dumps(metadata)

        # get version number
        ver_ids = self.extension.versions.order_by('-version')
        try:
            ver_id = ver_ids[0].version + 1
        except IndexError:
            # New extension, no versions yet
            ver_id = 1

        self.version = ver_id

        # ManyToManyField requires a PK, so we need to save.
        self.save()

        for sv_string in metadata.pop('shell-version', []):
            sv = ShellVersion.objects.get_for_version_string(sv_string)
            self.shell_versions.add(sv)

        self.save()

    def get_status_class(self):
        return STATUSES[self.status].lower()

submitted_for_review = Signal(providing_args=["version"])
reviewed = Signal(providing_args=["version", "review"])
status_changed = Signal(providing_args=["version", "log"])
