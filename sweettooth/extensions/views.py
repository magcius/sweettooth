
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

from extensions import models
from extensions.forms import UploadForm

from decorators import ajax_view, model_view
from utils import render

def shell_download(request, uuid):
    pk = request.GET['version_tag']
    if pk == 'latest':
        extension = get_object_or_404(models.Extension, uuid=uuid)
        version = extension.latest_version

    else:
        version = get_object_or_404(models.ExtensionVersion, pk=pk)
        extension = version.extension

        if version.extension.uuid != uuid:
            raise Http404()

    if version.status != models.STATUS_ACTIVE:
        return HttpResponseForbidden()

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

def get_versions_for_version_strings(version_strings):
    for version_string in version_strings:
        version = models.ShellVersion.objects.lookup_for_version_string(version_string, ignore_micro=True)
        if version is None:
            continue
        yield version

        base_version = version.base_version
        if base_version is None:
            continue
        yield base_version

def ajax_query_params_query(request):
    query_params = {}

    version_strings = request.GET.getlist('shell_version')
    if version_strings and version_strings != ['all']:
        versions = set(get_versions_for_version_strings(version_strings))
        query_params['versions__shell_versions__in'] = versions

    uuids = request.GET.getlist('uuid')
    if uuids:
        query_params['uuid__in'] = uuids

    queryset = models.Extension.objects.visible().filter(**query_params)

    sort = request.GET.get('sort', 'popularity')
    sort = dict(recent='created').get(sort, sort)
    if sort not in ('created', 'downloads', 'popularity', 'name'):
        raise Http404()

    queryset = queryset.order_by(sort)

    # sort by DESC for name, ASC for everything else
    default_order = dict(name='asc').get(sort, 'desc')

    if request.GET.get('order', default_order) == 'desc':
        queryset = queryset.reverse()

    return queryset

@ajax_view
def ajax_extensions_list(request):
    queryset = ajax_query_params_query(request)

    paginator = Paginator(queryset, 10)
    page = request.GET.get('page', 1)
    try:
        page_number = int(page)
    except ValueError:
        if page == 'last':
            page_number = paginator.num_pages
        else:
            # Page is not 'last', nor can it be converted to an int.
            raise Http404()
    try:
        page_obj = paginator.page(page_number)
    except InvalidPage:
        raise Http404()

    context = dict(paginator=paginator,
                   page_obj=page_obj,
                   extension_list=page_obj.object_list)

    return dict(html=render_to_string('extensions/list_bare.html', context),
                numpages = paginator.num_pages)

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
        # If it's unreviewed and unlocked, this is a preview
        # for pre-lock.
        is_preview = True

        # Don't allow anybody (even moderators) to peek pre-lock.
        if extension.creator != request.user:
            raise Http404()

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
def ajax_submit_and_lock_view(request, obj):
    if not obj.extension.user_can_edit(request.user):
        return HttpResponseForbidden()

    if obj.status != models.STATUS_NEW:
        return HttpResponseForbidden()

    obj.status = models.STATUS_LOCKED
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

def ajax_details(extension):
    return dict(uuid = extension.uuid,
                name = extension.name,
                creator = extension.creator.username,
                link = reverse('extensions-detail', kwargs=dict(pk=extension.pk)),
                icon = extension.icon.url,
                shell_version_map = extension.visible_shell_version_map_json)

@ajax_view
def ajax_details_view(request):
    uuid = request.GET.get('uuid', None)
    version = request.GET.get('version', None)

    if uuid is None:
        raise Http404()

    extension = get_object_or_404(models.Extension, uuid=uuid)
    details = ajax_details(extension)

    if version is not None:
        version = extension.versions.get(version=version)
        details['pk'] = version.pk

    return details

@ajax_view
def ajax_query_view(request):
    return [ajax_details(e) for e in ajax_query_params_query(request)]

@ajax_view
def ajax_set_status_view(request, newstatus):
    pk = request.GET['pk']

    version = get_object_or_404(models.ExtensionVersion, pk=pk)
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

            sid = transaction.savepoint()

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
                transaction.savepoint_rollback(sid)
            else:
                transaction.savepoint_commit(sid)

                version = models.ExtensionVersion.objects.create(extension=extension,
                                                                 source=file_source,
                                                                 status=models.STATUS_NEW)
                version.parse_metadata_json(metadata)
                version.replace_metadata_json()

                return redirect('extensions-version-detail',
                                pk=version.pk,
                                ext_pk=extension.pk,
                                slug=extension.slug)

    else:
        form = UploadForm()

    return render(request, 'extensions/upload.html', dict(form=form,
                                                          errors=errors,
                                                          extra_debug=extra_debug))
