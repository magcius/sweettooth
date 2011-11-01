
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, Http404
from django.shortcuts import get_object_or_404, redirect
from sorl.thumbnail.shortcuts import get_thumbnail

from extensions import models
from extensions.forms import UploadForm

from decorators import ajax_view, model_view, post_only_view
from utils import render

def download(request, uuid):
    pk = request.GET['version_tag']
    if pk == 'latest':
        extension = get_object_or_404(models.Extension, uuid=uuid)
        version = extension.latest_version

    else:
        version = get_object_or_404(models.ExtensionVersion, pk=pk)

        if version.extension.uuid != uuid:
            raise Http404()

    if version.status != models.STATUS_ACTIVE:
        return HttpResponseForbidden()

    return redirect(version.source.url)

# Even though this is showing a version, the PK matches an extension
@model_view(models.Extension)
def extension_latest_version_view(request, obj, **kwargs):
    extension, version = obj, obj.latest_version

    if version is None:
        raise Http404()

    # Redirect if we don't match the slug.
    slug = kwargs.get('slug')

    if slug != extension.slug:
        kwargs.update(dict(slug=extension.slug,
                           pk=extension.pk))
        return redirect('extensions-detail', **kwargs)

    # If the user can edit the model, let him do so.
    if extension.user_has_access(request.user):
        template_name = "extensions/detail_edit.html"
    else:
        template_name = "extensions/detail.html"

    status = version.status
    context = dict(version = version,
                   extension = extension,
                   is_visible = status in models.VISIBLE_STATUSES,
                   status = status)
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
    if extension.user_has_access(request.user):
        template_name = "extensions/detail_edit.html"
    else:
        template_name = "extensions/detail.html"

    context = dict(version = version,
                   extension = extension,
                   is_preview = is_preview,
                   is_visible = status in models.VISIBLE_STATUSES,
                   is_rejected = status in models.REJECTED_STATUSES,
                   status = status)

    if extension.latest_version is not None:
        context['old_version'] = version.version < extension.latest_version.version
    return render(request, template_name, context)

@ajax_view
@post_only_view
@model_view(models.ExtensionVersion)
def ajax_submit_and_lock_view(request, obj):
    if not obj.extension.user_has_access(request.user):
        return HttpResponseForbidden()

    if obj.status != models.STATUS_NEW:
        return HttpResponseForbidden()

    obj.status = models.STATUS_LOCKED
    obj.save()

    models.submitted_for_review.send(sender=request, request=request, version=obj)

@ajax_view
@post_only_view
@model_view(models.Extension)
def ajax_inline_edit_view(request, obj):
    if not obj.user_has_access(request.user):
        return HttpResponseForbidden()

    key = request.POST['id']
    value = request.POST['value']
    if key.startswith('extension_'):
        key = key[len('extension_'):]

    whitelist = 'name', 'description', 'url'
    if key not in whitelist:
        return HttpResponseForbidden()

    setattr(obj, key, value)
    obj.save()

    return value

@ajax_view
@post_only_view
@model_view(models.Extension)
def ajax_upload_screenshot_view(request, obj):
    obj.screenshot = request.FILES['file']
    obj.save()
    return get_thumbnail(obj.screenshot, request.GET['geometry']).url

@ajax_view
@post_only_view
@model_view(models.Extension)
def ajax_upload_icon_view(request, obj):
    obj.icon = request.FILES['file']
    obj.save()
    return obj.icon.url

def ajax_details(extension):
    return dict(pk = extension.pk,
                uuid = extension.uuid,
                name = extension.name,
                creator = extension.creator.username,
                link = reverse('extensions-detail', kwargs=dict(pk=extension.pk)),
                icon = extension.icon.url)

@ajax_view
def ajax_details_view(request):
    uuid = request.GET.get('uuid', None)

    if uuid is None:
        raise Http404()

    extension = get_object_or_404(models.Extension, uuid=uuid)
    return ajax_details(extension)

@ajax_view
def ajax_query_view(request):
    query_params = {}

    versions = request.GET.getlist('shell_version')
    if versions:
        versions = [models.ShellVersion.objects.lookup_for_version_string(v) for v in versions]
        versions = [v for v in versions if v is not None]
        query_params['versions__shell_versions__in'] = versions

    uuids = request.GET.getlist('uuid')
    if uuids:
        query_params['uuid__in'] = uuids

    if not query_params:
        raise Http404()

    extensions = models.Extension.objects.filter(**query_params)
    return [ajax_details(e) for e in extensions]

@login_required
def upload_file(request, pk):
    if pk is None:
        extension = models.Extension(creator=request.user)
    else:
        extension = models.Extension.objects.get(pk=pk)
        if extension.creator != request.user:
            return HttpResponseForbidden()

    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_source = form.cleaned_data['source']

            try:
                metadata = models.parse_zipfile_metadata(file_source)
                uuid = metadata['uuid']
            except (models.InvalidExtensionData, KeyError), e:
                messages.error(request, "Invalid extension data.")

                if pk is not None:
                    return redirect('extensions-upload-file', pk=pk)
                else:
                   return redirect('extensions-upload-file')

            existing = models.Extension.objects.filter(uuid=uuid)
            if pk is None and existing.exists():
                # Error out if we already have an extension with the same
                # uuid -- or correct their mistake if they're the same user.
                ext = existing.get()
                if request.user == ext.creator:
                    return upload_file(request, ext.pk)
                else:
                    messages.error(request, "An extension with that UUID has already been added.")
                    return redirect('extensions-upload-file')

            version = models.ExtensionVersion()
            version.extension = extension
            version.parse_metadata_json(metadata)

            extension.creator = request.user
            extension.save()

            version.extension = extension
            version.source = file_source
            version.status = models.STATUS_NEW
            version.save()

            version.replace_metadata_json()

            return redirect('extensions-version-detail',
                            pk=version.pk,
                            ext_pk=extension.pk,
                            slug=extension.slug)
    else:
        form = UploadForm()

    return render(request, 'extensions/upload.html', dict(form=form))
