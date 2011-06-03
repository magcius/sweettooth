
from django.shortcuts import render, get_object_or_404
from browse.models import Extension

def index(request):
    extensions = Extension.objects.all()
    return render(request, 'index.html', dict(extensions=extensions))

def detail(request, slug):
    extension = get_object_or_404(Extension, slug=slug)
    return render(request, 'detail.html', dict(extension=extension))
