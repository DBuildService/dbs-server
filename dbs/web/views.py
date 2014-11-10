from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

from django.shortcuts import render
from django.views.generic import ListView

from ..models import Image, Task

def home(request):
    return render(request, 'home.html')


class ImageListView(ListView):
    model = Image

image_list = ImageListView.as_view()



class TaskListView(ListView):
    model = Task

task_list = TaskListView.as_view()

#class NewImage()
#    model = Image
