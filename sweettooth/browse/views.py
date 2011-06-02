
from django.shortcuts import render_to_response
from browse.models import Extension

def index(request):
    extensions = Extension.objects.all()
    return render_to_response('index.html', dict(extensions=extensions))
