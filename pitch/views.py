from django.http import Http404
from django.shortcuts import render
from django.utils.translation import gettext
from django.views import generic
from pitch.models import Pitch


# Create your views here.
def index(request):
    context = {"title": gettext("Home Page")}
    return render(request, "index.html", context=context)


class PitchListView(generic.ListView):
    model = Pitch
    paginate_by = 10

    def get_queryset(self):
        return Pitch.objects.all()

    def get_context_data(self, **kwargs):
        context = super(PitchListView, self).get_context_data(**kwargs)
        pitches = context["pitch_list"]
        for pitch in pitches:
            if pitch.image.all().exists():
                pitch.banner = pitch.image.all()[0].image.url
            else:
                pitch.banner = "/uploads/uploads/default-image.jpg"
            pitch.surface = pitch.get_label_grass()
            pitch.size = pitch.get_label_size()
        context["pitch_list"] = pitches
        return context


class PitchDetailView(generic.DetailView):
    model = Pitch

    def pitch_detail_view(request, primary_key):
        try:
            pitch = Pitch.objects.get(pk=primary_key)
        except Pitch.DoesNotExist:
            raise Http404("Pitch does not exist")

        return render(request, "pitch/pitch_detail.html", context={"pitch": pitch})

    def get_context_data(self, **kwargs):
        context = super(PitchDetailView, self).get_context_data(**kwargs)
        context["images"] = context["pitch"].image.all()

        return context
