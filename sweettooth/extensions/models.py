
import json

from zipfile import ZipFile, BadZipfile

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.db import models
from django.dispatch import Signal

import autoslug
import re

(STATUS_UNREVIEWED,
 STATUS_REJECTED,
 STATUS_INACTIVE,
 STATUS_ACTIVE,
 STATUS_WAITING) = xrange(5)

STATUSES = {
    STATUS_UNREVIEWED: u"Unreviewed",
    STATUS_REJECTED: u"Rejected",
    STATUS_INACTIVE: u"Inactive",
    STATUS_ACTIVE: u"Active",
    STATUS_WAITING: u"Waiting for author",
}

def validate_uuid(uuid):
    if re.match(r'[-a-zA-Z0-9@._]+$', uuid) is None:
        return False

    # Don't blacklist "gnome.org" - we don't want to eliminate
    # world-of-gnome.org or something like that.
    if re.search(r'[.@]gnome\.org$', uuid) is not None:
        return False

    return True

class ExtensionManager(models.Manager):
    def visible(self):
        return self.filter(versions__status=STATUS_ACTIVE).distinct()

    def create_from_metadata(self, metadata, **kwargs):
        instance = self.model(**kwargs)
        instance.parse_metadata_json(metadata)
        instance.save()
        return instance

def build_shell_version_map(versions):
    shell_version_map = {}
    for version in versions:
        for shell_version in version.shell_versions.all():
            key = shell_version.version_string
            if key not in shell_version_map:
                shell_version_map[key] = version

            if version.version > shell_version_map[key].version:
                shell_version_map[key] = version

    for key, version in shell_version_map.iteritems():
        shell_version_map[key] = dict(pk = version.pk,
                                      version = version.version)

    return shell_version_map

class Extension(models.Model):
    name = models.CharField(max_length=200)
    uuid = models.CharField(max_length=200, unique=True, db_index=True)
    slug = autoslug.AutoSlugField(populate_from="name")
    creator = models.ForeignKey(User, db_index=True)
    description = models.TextField(blank=True)
    url = models.URLField(verify_exists=False, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    downloads = models.PositiveIntegerField(default=0)
    popularity = models.IntegerField(default=0)

    class Meta:
        permissions = (
            ("can-modify-data", "Can modify extension data"),
        )

    def make_screenshot_filename(self, filename=None):
        return "screenshots/screenshot_%d.png" % (self.pk,)

    screenshot = models.ImageField(upload_to=make_screenshot_filename, blank=True)

    def make_icon_filename(self, filename=None):
        return "icons/icon_%d.png" % (self.pk,)

    icon = models.ImageField(upload_to=make_icon_filename, blank=True, default="/static/images/plugin.png")

    objects = ExtensionManager()

    def __unicode__(self):
        return self.uuid

    def parse_metadata_json(self, metadata):
        self.name = metadata.pop('name', "")
        self.description = metadata.pop('description', "")
        self.url = metadata.pop('url', "")
        self.uuid = metadata['uuid']

    def clean(self):
        from django.core.exceptions import ValidationError

        if not validate_uuid(self.uuid):
            raise ValidationError("Your extension has an invalid UUID")

    def save(self, replace_metadata_json=True, *args, **kwargs):
        super(Extension, self).save(*args, **kwargs)
        if replace_metadata_json:
            for version in self.versions.all():
                if version.source:
                    try:
                        version.replace_metadata_json()
                    except BadZipfile, e:
                        # Ignore bad zipfiles, we don't care
                        pass

    def get_absolute_url(self):
        return reverse('extensions-detail', kwargs=dict(pk=self.pk,
                                                        slug=self.slug))

    def user_can_edit(self, user):
        if user == self.creator:
            return True
        if user.has_perm('extensions.can-modify-data'):
            return True
        return False

    @property
    def first_line_of_description(self):
        if not self.description:
            return ""
        return self.description.splitlines()[0]

    @property
    def visible_versions(self):
        return self.versions.filter(status=STATUS_ACTIVE)

    @property
    def latest_version(self):
        try:
            return self.visible_versions.latest()
        except ExtensionVersion.DoesNotExist:
            return None

    @property
    def visible_shell_version_map(self):
        return build_shell_version_map(self.visible_versions)

class ExtensionPopularityItem(models.Model):
    extension = models.ForeignKey(Extension, db_index=True,
                                  related_name='popularity_items')
    offset = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)

class InvalidShellVersion(Exception):
    pass


def parse_version_string(version_string):
    version = version_string.split('.')

    try:
        major, minor = version[:2]
        major, minor = int(major), int(minor)
    except ValueError, e:
        raise InvalidShellVersion()

    if len(version) in (3, 4):
        # 3.0.1, 3.1.4
        try:
            point = int(version[2])
        except ValueError, e:
            raise InvalidShellVersion()

    elif len(version) == 2 and minor % 2 == 0:
        # 3.0, 3.2
        point = -1
    else:
        # Two-digit odd versions are illegal: 3.1, 3.3
        raise InvalidShellVersion()

    return major, minor, point

class ShellVersionManager(models.Manager):
    def lookup_for_version_string(self, version_string):
        major, minor, point = parse_version_string(version_string)
        try:
            return self.get(major=major, minor=minor, point=point)
        except self.model.DoesNotExist:
            return None

    def get_for_version_string(self, version_string):
        major, minor, point = parse_version_string(version_string)
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

    if zipfile.testzip() is not None:
        raise InvalidExtensionData("Invalid zip file")

    total_uncompressed = sum(i.file_size for i in zipfile.infolist())
    if total_uncompressed > 5*1024*1024: # 5 MB
        raise InvalidExtensionData("Zip file is too large")

    try:
        metadata = json.load(zipfile.open('metadata.json', 'r'))
    except KeyError:
        # no metadata.json in archive, raise error
        raise InvalidExtensionData("Missing metadata.json")
    except ValueError:
        # invalid JSON file, raise error
        raise InvalidExtensionData("Invalid JSON data")

    zipfile.close()
    return metadata

# uuid max length + suffix max length
filename_max_length = Extension._meta.get_field('uuid').max_length + len(".v000.shell-version.zip")

class ExtensionVersionManager(models.Manager):
    def unreviewed(self):
        return self.filter(status=STATUS_UNREVIEWED)

    def waiting(self):
        return self.filter(status=STATUS_WAITING)

    def visible(self):
        return self.filter(status=STATUS_ACTIVE)

class ExtensionVersion(models.Model):
    extension = models.ForeignKey(Extension, related_name="versions")
    version = models.IntegerField(default=0)
    extra_json_fields = models.TextField()
    status = models.PositiveIntegerField(choices=STATUSES.items())
    shell_versions = models.ManyToManyField(ShellVersion)

    class Meta:
        unique_together = ('extension', 'version'),
        get_latest_by = 'version'

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
            version     = self.version,
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

    def save(self, *args, **kwargs):
        assert self.extension is not None

        if self.version == 0:
            # Get version number
            try:
                # Don't use extension.latest_version, as that will
                # give us the latest visible version.
                self.version = self.extension.versions.latest().version + 1
            except self.DoesNotExist:
                self.version = 1

        super(ExtensionVersion, self).save(*args, **kwargs)

    def parse_metadata_json(self, metadata):
        """
        Given the contents of a metadata.json file, fill in the fields
        of the version and associated extension.

        NOTE: This needs to be called after this has been saved, as we
        need a PK to be able to add ourselves to a PK.
        """

        self.extra_json_fields = json.dumps(metadata)

        for sv_string in metadata.pop('shell-version', []):
            try:
                sv = ShellVersion.objects.get_for_version_string(sv_string)
            except InvalidShellVersion:
                # For now, ignore invalid shell versions, rather than
                # causing a fit.
                continue
            else:
                self.shell_versions.add(sv)

    def get_absolute_url(self):
        return self.extension.get_absolute_url()

    def get_status_class(self):
        return STATUSES[self.status].lower()

    def is_approved(self):
        return self.status in (STATUS_ACTIVE, STATUS_INACTIVE)

    def is_active(self):
        return self.status == STATUS_ACTIVE

    def is_inactive(self):
        return self.status == STATUS_INACTIVE

submitted_for_review = Signal(providing_args=["request", "version"])
reviewed = Signal(providing_args=["request", "version", "review"])
extension_updated = Signal(providing_args=["extension"])
