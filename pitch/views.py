from django.shortcuts import render
from django.utils.translation import gettext



# Create your views here.
def index(request):
    context = {"title": gettext("Home Page")}
    return render(request, "index.html", context=context)
