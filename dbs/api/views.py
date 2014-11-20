from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

import json
import logging

from django.core.exceptions import (
    ObjectDoesNotExist, PermissionDenied, SuspiciousOperation
)
from django.db.models import Model, QuerySet
from django.http import JsonResponse
from django.views.generic import View
from django.views.generic.edit import FormMixin
from functools import partial

from .core import (
    new_image_callback, move_image_callback,
)
from .forms import NewImageForm, MoveImageForm
from ..task_api import TaskApi
from ..models import Image, Task, TaskData


logger = logging.getLogger(__name__)
builder_api = TaskApi()


def translate_args(translation_dict, values):
    """
    translate keys in dict values using translation_dict
    """
    response = {}
    for key, value in values.items():
        try:
            response[translation_dict[key]] = value
        except KeyError:
            response[key] = value
    return response



class ModelJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Model):
            return obj.__json__()
        elif isinstance(obj, QuerySet):
            return [o.__json__() for o in obj]
        else:
            return super(ModelJSONEncoder, self).default(obj)



class JsonView(View):
    """
    Overrides dispatch method to always return JsonResponse.
    """
    def dispatch(self, request, *args, **kwargs):
        try:
            response = super(JsonView, self).dispatch(request, *args, **kwargs)
            if not isinstance(response, JsonResponse):
                response = JsonResponse(response, encoder=ModelJSONEncoder, safe=False)
        except ObjectDoesNotExist:
            logger.warning('Not Found: %s', request.path,
                extra={'status_code': 404, 'request': request})
            response = JsonResponse({'error': 'Not Found'})
            response.status_code = 404
        except PermissionDenied:
            logger.warning('Forbidden (Permission denied): %s', request.path,
                extra={'status_code': 403, 'request': request})
            response = JsonResponse({'error': 'Forbidden'})
            response.status_code = 403
        except SuspiciousOperation as e:
            logger.error(force_text(e),
                extra={'status_code': 400, 'request': request})
            response = JsonResponse({'error': 'Bad Request'})
            response.status_code = 400
        except SystemExit:
            # Allow sys.exit()
            raise
        except:
            logger.exception('Failed to handle request: %s', request.path,
                extra={'status_code': 500, 'request': request})
            response = JsonResponse({'error': 'Internal Server Error'})
            response.status_code = 500
        return response



class FormJsonView(FormMixin, JsonView):
    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        #self.args   = args
        #self.kwargs = kwargs
        form_class  = self.get_form_class()
        form        = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def put(self, *args, **kwargs):
        return self.post(*args, **kwargs)

    def form_valid(self, form):
        return {'message': 'OK'}

    def form_invalid(self, form):
        return {'errors': form.errors}

    def get_form_kwargs(self):
        kwargs = super(FormJsonView, self).get_form_kwargs()
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': json.loads(self.request.body),
            })
        return kwargs



class ImageStatusCall(JsonView):
    def get(self, request, image_id):
        img = Image.objects.get(hash=image_id)
        return {
            'image_id': image_id,
            'status': img.get_status_display(),
        }



class ImageInfoCall(JsonView):
    def get(self, request, image_id):
        return Image.objects.get(hash=image_id)



class ImageDepsCall(JsonView):
    def get_deps(self, image):
        return {
            'image_id': image.hash,
            'deps': [self.get_deps(i) for i in image.children()],
        }
    def get(self, request, image_id):
        image = Image.objects.get(hash=image_id)
        return self.get_deps(image)



class ListImagesCall(JsonView):
    def get(self, request):
        return Image.objects.all()



class TaskStatusCall(JsonView):
    def get(self, request, task_id):
        return Task.objects.get(id=task_id)



class ListTasksCall(JsonView):
    def get(self, request):
        return Task.objects.all()



class NewImageCall(FormJsonView):
    form_class  = NewImageForm

    def form_valid(self, form):
        """ initiate a new build """
        cleaned_data = form.cleaned_data
        owner = 'testuser'  # XXX: hardcoded
        logger.debug('cleaned_data = %s', cleaned_data)
        local_tag = '%s/%s' % (owner, cleaned_data['tag'])
        td = TaskData(json=json.dumps(cleaned_data))
        td.save()
        t = Task(builddev_id='buildroot-fedora', status=Task.STATUS_PENDING,
                 type=Task.TYPE_BUILD, owner=owner, task_data=td)
        t.save()
        cleaned_data.update({'build_image': 'buildroot-fedora', 'local_tag': local_tag,
                     'callback': partial(new_image_callback, t.id)})
        task_id = builder_api.build_docker_image(**cleaned_data)
        t.celery_id = task_id
        t.save()
        return {'task_id': t.id}



class MoveImageCall(FormJsonView):
    form_class  = MoveImageForm

    def form_valid(self, form):
        data = form.cleaned_data
        data['image_id'] = self.kwargs['image_id']
        td = TaskData(json=json.dumps(data))
        td.save()
        owner = 'testuser'  # XXX: hardcoded
        t = Task(type=Task.TYPE_MOVE, owner=owner, task_data=td)
        t.save()
        data['callback'] = partial(move_image_callback, t.id)
        task_id = builder_api.push_docker_image(**data)
        t.celery_id = task_id
        t.save()
        return {'task_id': t.id}



class RebuildImageCall(JsonView):
    """ rebuild provided image; use same response as new_image """
    def post(self, request, image_id):
        post_args   = json.loads(self.request.body)
        try:
            data = json.loads(
                Image.objects.get(hash=image_id).task.task_data.json
            )
        except (ObjectDoesNotExist, AttributeError) as e:
            logger.error(repr(e))
            raise ErrorDuringRequest('Image does not exist or was not built from task.')
        else:
            if post_args:
                data.update(post_args)
        data['image_id'] = image_id
        td = TaskData(json=json.dumps(data))
        td.save()
        owner = 'testuser'  # XXX: hardcoded
        t = Task(type=Task.TYPE_MOVE, owner=owner, task_data=td)
        t.save()
        data['callback'] = partial(move_image_callback, t.id)
        task_id = builder_api.push_docker_image(**data)
        t.celery_id = task_id
        t.save()
        return {'task_id': t.id}



class InvalidateImageCall(JsonView):
    def post(self, request, image_id):
        count = Image.objects.invalidate(image_id)
        return {'message': 'Invalidated {} images.'.format(count)}


