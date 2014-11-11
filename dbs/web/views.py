from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView

from ..models import Image, Task

def home(request):
    return render(request, 'home.html')


class ImageListView(ListView):
    model = Image

image_list = ImageListView.as_view()



class TaskListView(ListView):
    model = Task

task_list = TaskListView.as_view()


class ImageView(DetailView):
    model = Image

    def get_object(self):
        return get_object_or_404(Image, hash=self.kwargs.get('hash', None))

image_detail = ImageView.as_view()
