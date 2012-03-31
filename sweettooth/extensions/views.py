
from math import ceil

from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, InvalidPage
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseForbidden, HttpResponseServerError, Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils import simplejson as json
from django.views.decorators.http import require_POST
from sorl.thumbnail.shortcuts import get_thumbnail

from extensions import models, search
from extensions.forms import UploadForm

from decorators import ajax_view, model_view
from utils import render

def get_versions_for_version_strings(version_strings):
    def get_version(major, minor, point):
        try:
            return models.ShellVersion.objects.get(major=major, minor=minor, point=point)
        except models.ShellVersion.DoesNotExist:
            return None

    for version_string in version_strings:
        try:
            major, minor, point = models.parse_version_string(version_string, ignore_micro=True)
        except models.InvalidShellVersion:
            continue

        version = get_version(major, minor, point)
        if version:
            yield version

        # If we already have a base version, don't bother querying it again...
        if point == -1:
            continue

        base_version = get_version(major, minor, -1)
        if base_version:
            yield base_version

def grab_proper_extension_version(extension, shell_version):
    shell_versions = set(get_versions_for_version_strings([shell_version]))
    if not shell_versions:
        return None

    versions = extension.visible_versions.filter(shell_versions__in=shell_versions)
    if versions.count() < 1:
        return None
    else:
        return versions.order_by('-version')[0]

def find_extension_version_from_params(extension, params):
    vpk = params.get('version_tag', '')
    shell_version = params.get('shell_version', '')

    if vpk:
        try:
            return extension.visible_versions.get(pk=int(vpk))
        except models.ExtensionVersion.DoesNotExist:
            return None
    elif shell_version:
        return grab_proper_extension_version(extension, shell_version)
    else:
        return None

def shell_download(request, uuid):
    extension = get_object_or_404(models.Extension.objects.visible(), uuid=uuid)
    version = find_extension_version_from_params(extension, request.GET)

    extension.downloads += 1
    extension.save(replace_metadata_json=False)

    return redirect(version.source.url)

@ajax_view
@require_POST
def shell_update(request):
    installed = json.loads(request.POST['installed'])
    operations = {}

    for uuid, version in installed.iteritems():
        try:
            extension = models.Extension.objects.get(uuid=uuid)
        except models.Extension.DoesNotExist:
            continue

        try:
            version_obj = extension.versions.get(version=version)
        except models.ExtensionVersion.DoesNotExist:
            # The user may have a newer version than what's on the site.
            continue

        latest_version = extension.latest_version

        if latest_version is None:
            operations[uuid] = dict(operation="blacklist")

        elif version < latest_version.version:
            operations[uuid] = dict(operation="upgrade",
                                    version=extension.latest_version.pk)

        elif version_obj.status in models.REJECTED_STATUSES:
            operations[uuid] = dict(operation="downgrade",
                                    version=extension.latest_version.pk)

    return operations

def ajax_query_params_query(request, n_per_page=10):
    version_qs = models.ExtensionVersion.objects.visible()

    version_strings = request.GET.getlist('shell_version')
    if version_strings and version_strings != ['all']:
        versions = set(get_versions_for_version_strings(version_strings))
        version_qs = version_qs.filter(shell_versions__in=versions)

    queryset = models.Extension.objects.distinct().filter(versions__in=version_qs)

    uuids = request.GET.getlist('uuid')
    if uuids:
        queryset = queryset.filter(uuid__in=uuids)

    sort = request.GET.get('sort', 'popularity')
    sort = dict(recent='created').get(sort, sort)
    if sort not in ('created', 'downloads', 'popularity', 'name'):
        raise Http404()

    queryset = queryset.order_by(sort)

    # Sort by ASC for name, DESC for everything else.
    if sort == 'name':
        default_order = 'asc'
    else:
        default_order = 'desc'

    order = request.GET.get('order', default_order)
    queryset.query.standard_ordering = (order == 'asc')

    # Paginate the query
    paginator = Paginator(queryset, n_per_page)
    page = request.GET.get('page', 1)
    try:
        page_number = int(page)
    except ValueError:
        raise Http404()

    try:
        page_obj = paginator.page(page_number)
    except InvalidPage:
        raise Http404()

    return page_obj.object_list, paginator.num_pages

def ajax_query_search_query(request, n_per_page=10):
    querystring = request.GET.get('search', '')

    enquire = search.enquire(querystring)

    page = request.GET.get('page', 1)
    try:
        offset = (int(page) - 1) * n_per_page
    except ValueError:
        raise Http404()

    mset = enquire.get_mset(offset, n_per_page)
    pks = [match.document.get_data() for match in mset]

    num_pages = int(ceil(float(mset.get_matches_estimated()) / n_per_page))

    # filter doesn't guarantee an order, so we need to get all the
    # possible models then look them up to get the ordering
    # returned by xapian. This hits the database all at once, rather
    # than pagesize times.
    extension_lookup = {}
    for extension in models.Extension.objects.filter(pk__in=pks):
        extension_lookup[str(extension.pk)] = extension

    extensions = [extension_lookup[pk] for pk in pks]

    return extensions, num_pages

@ajax_view
def ajax_query_view(request):
    if request.GET.get('search',  ''):
        func = ajax_query_search_query
    else:
        func = ajax_query_params_query

    object_list, num_pages = func(request)

    return dict(extensions=[ajax_details(e) for e in object_list],
                numpages=num_pages)

@model_view(models.Extension)
def extension_view(request, obj, **kwargs):
    extension, versions = obj, obj.visible_versions

    if versions.count() == 0 and not extension.user_can_edit(request.user):
        raise Http404()

    # Redirect if we don't match the slug.
    slug = kwargs.get('slug')

    if slug != extension.slug:
        kwargs.update(dict(slug=extension.slug,
                           pk=extension.pk))
        return redirect('extensions-detail', **kwargs)

    # If the user can edit the model, let him do so.
    if extension.user_can_edit(request.user):
        template_name = "extensions/detail_edit.html"
    else:
        template_name = "extensions/detail.html"

    context = dict(shell_version_map = obj.visible_shell_version_map_json,
                   extension = extension,
                   all_versions = extension.versions.order_by('-version'),
                   is_visible = True,
                   is_multiversion = True)
    return render(request, template_name, context)

@model_view(models.ExtensionVersion)
def extension_version_view(request, obj, **kwargs):
    extension, version = obj.extension, obj

    is_preview = False

    status = version.status
    if status == models.STATUS_NEW:
        # If it's new, this is a preview before it's submitted
        is_preview = True

    # Redirect if we don't match the slug or extension PK.
    slug = kwargs.get('slug')
    extpk = kwargs.get('ext_pk')
    try:
        extpk = int(extpk)
    except ValueError:
        extpk = None

    if slug != extension.slug or extpk != extension.pk:
        kwargs.update(dict(slug=extension.slug,
                           ext_pk=extension.pk))
        return redirect('extensions-version-detail', **kwargs)

    # If the user can edit the model, let him do so.
    if extension.user_can_edit(request.user):
        template_name = "extensions/detail_edit.html"
    else:
        template_name = "extensions/detail.html"

    version_obj = dict(pk = version.pk, version = version.version)
    shell_version_map = dict((sv.version_string, version_obj) for sv in version.shell_versions.all())

    context = dict(version = version,
                   extension = extension,
                   shell_version_map = json.dumps(shell_version_map),
                   is_preview = is_preview,
                   is_visible = status in models.VISIBLE_STATUSES,
                   is_rejected = status in models.REJECTED_STATUSES,
                   is_new_extension = (extension.versions.count() == 1),
                   status = status)

    if extension.latest_version is not None:
        context['old_version'] = version.version < extension.latest_version.version
    return render(request, template_name, context)

@require_POST
@ajax_view
def ajax_adjust_popularity_view(request):
    uuid = request.POST['uuid']
    action = request.POST['action']

    extension = models.Extension.objects.get(uuid=uuid)
    pop = models.ExtensionPopularityItem(extension=extension)

    if action == 'enable':
        pop.offset = +1
    elif action == 'disable':
        pop.offset = -1
    else:
        return HttpResponseServerError()

    pop.save()

@ajax_view
@require_POST
@model_view(models.ExtensionVersion)
def ajax_submit_extension_view(request, obj):
    if not obj.extension.user_can_edit(request.user):
        return HttpResponseForbidden()

    if obj.status != models.STATUS_NEW:
        return HttpResponseForbidden()

    obj.status = models.STATUS_UNREVIEWED
    obj.save()

    models.submitted_for_review.send(sender=request, request=request, version=obj)

@ajax_view
@require_POST
@model_view(models.Extension)
def ajax_inline_edit_view(request, obj):
    if not obj.user_can_edit(request.user):
        return HttpResponseForbidden()

    key = request.POST['id']
    value = request.POST['value']
    if key.startswith('extension_'):
        key = key[len('extension_'):]

    if key == 'name':
        obj.name = value
    elif key == 'description':
        obj.description = value
    elif key == 'url':
        obj.url = value
    else:
        return HttpResponseForbidden()

    obj.save()

    return value

@ajax_view
@require_POST
@model_view(models.Extension)
def ajax_upload_screenshot_view(request, obj):
    obj.screenshot = request.FILES['file']
    obj.save(replace_metadata_json=False)
    return get_thumbnail(obj.screenshot, request.GET['geometry']).url

@ajax_view
@require_POST
@model_view(models.Extension)
def ajax_upload_icon_view(request, obj):
    obj.icon = request.FILES['file']
    obj.save(replace_metadata_json=False)
    return obj.icon.url

def ajax_details(extension, version=None):
    details = dict(uuid = extension.uuid,
                   name = extension.name,
                   creator = extension.creator.username,
                   creator_url = reverse('auth-profile', kwargs=dict(user=extension.creator.username)),
                   description = extension.description,
                   link = reverse('extensions-detail', kwargs=dict(pk=extension.pk)),
                   icon = extension.icon.url,
                   shell_version_map = extension.visible_shell_version_map)

    if version is not None:
        download_url = reverse('extensions-shell-download', kwargs=dict(uuid=extension.uuid))
        details['version'] = version.version
        details['version_tag'] = version.pk
        details['download_url'] = "%s?version_tag=%d" % (download_url, version.pk)
    return details

@ajax_view
def ajax_details_view(request):
    uuid = request.GET.get('uuid', None)
    pk = request.GET.get('pk', None)

    if uuid is not None:
        extension = get_object_or_404(models.Extension.objects.visible(), uuid=uuid)
    elif pk is not None:
        extension = get_object_or_404(models.Extension.objects.visible(), pk=pk)
    else:
        raise Http404()

    version = find_extension_version_from_params(extension, request.GET)
    return ajax_details(extension, version)

@ajax_view
def ajax_set_status_view(request, newstatus):
    pk = request.GET['pk']

    version = get_object_or_404(models.ExtensionVersion.objects.visible(), pk=pk)
    extension = version.extension

    if not extension.user_can_edit(request.user):
        return HttpResponseForbidden()

    version.status = newstatus
    version.save()

    context = dict(version=version,
                   extension=extension)

    return dict(svm=extension.visible_shell_version_map_json,
                mvs=render_to_string('extensions/multiversion_status.html', context))

@login_required
@transaction.commit_manually
def upload_file(request):
    errors = []
    extra_debug = None

    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_source = form.cleaned_data['source']

            try:
                metadata = models.parse_zipfile_metadata(file_source)
                uuid = metadata['uuid']
            except (models.InvalidExtensionData, KeyError), e:
                messages.error(request, "Invalid extension data: %s" % (e.message,))
                return redirect('extensions-upload-file')

            try:
                extension = models.Extension.objects.get(uuid=uuid)
            except models.Extension.DoesNotExist:
                extension = models.Extension.objects.create_from_metadata(metadata, creator=request.user)
            else:
                if request.user != extension.creator:
                    messages.error(request, "An extension with that UUID has already been added.")
                    return redirect('extensions-upload-file')

            try:
                extension.full_clean()
            except ValidationError, e:
                # Output a specialized error message for a common mistake:
                if getattr(e, 'message_dict', None) and 'url' in e.message_dict:
                    errors = [mark_safe("You have an invalid URL. Make sure your URL "
                                        "starts with <pre>http://</pre>")]
                else:
                    errors = e.messages

                extra_debug = repr(e)
                transaction.rollback()
            else:
                version = models.ExtensionVersion.objects.create(extension=extension,
                                                                 source=file_source,
                                                                 status=models.STATUS_NEW)
                version.parse_metadata_json(metadata)
                version.replace_metadata_json()
                version.save()

                transaction.commit()

                return redirect('extensions-version-detail',
                                pk=version.pk,
                                ext_pk=extension.pk,
                                slug=extension.slug)

    else:
        form = UploadForm()

    # XXX - context managers may dirty the connection, so we need
    # to force a clean state after this.
    response = render(request, 'extensions/upload.html', dict(form=form,
                                                              errors=errors,
                                                              extra_debug=extra_debug))

    transaction.set_clean()

    return response
