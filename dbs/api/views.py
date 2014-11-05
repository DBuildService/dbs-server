from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

import sys
import copy
import json
import socket
import logging

from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import View

from .core import build, rebuild, ErrorDuringRequest
from dbs.api.core import move_image
from ..models import Dockerfile, TaskData, Task, Rpms, Registry, YumRepo, Image, ImageRegistryRelation
from ..task_api import TaskApi


logger = logging.getLogger(__name__)
builder_api = TaskApi()


class ApiCall(View):
    required_args = []
    optional_args = []
    func_response = None
    error_response = None
    func = None

    def __init__(self, **kwargs):
        super(ApiCall, self).__init__(**kwargs)
        self.args = None  # POST args

    def process(self, **kwargs):
        # if you call it just like self.func, python will treat it as method, not as function
        try:
            func = self.func.im_func  # py2
        except AttributeError:
            func = self.func.__func__  # py3
        logger.debug("api callback: %s(%s, %s)", func.__name__, self.args, kwargs)
        try:
            self.func_response = func(self.args, **kwargs)
        except ErrorDuringRequest as ex:
            self.error_response = {'error': ex.message}
        except Exception as ex:
            logger.exception("Exception during processing request")
            self.error_response = {'error': repr(ex)}

    def validate_rest_input(self):
        # request.body -- requets sent as json
        # request.POST -- sent as application/*form*
        data_sources = []
        try:
            data_sources.append(json.loads(self.request.body))
        except ValueError:
            pass
        data_sources.append(self.request.POST)

        req_is_valid = False
        for source in data_sources:
            for req_arg in self.required_args:
                try:
                    source[req_arg]
                except KeyError:
                    req_is_valid = False
                    break
                req_is_valid = True
            if req_is_valid:
                break
        if not req_is_valid and self.required_args:
            raise RuntimeError("request is missing '%s'" % req_arg)
        for arg in source:
            if arg not in self.optional_args and arg not in self.required_args:
                raise RuntimeError("Invalid argument '%s' supplied" % arg)
        return source

    def compose_response(self):
        return self.func_response

    def do_request(self, request, **kwargs):
        logger.debug("request: %s", kwargs)  # first thing is request, dont log it
        self.process(**kwargs)
        if self.error_response:
            return JsonResponse(self.error_response)
        return JsonResponse(self.compose_response())

    def post(self, request, **kwargs):
        self.args = self.validate_rest_input()
        return self.do_request(request, **kwargs)

    def get(self, request, **kwargs):
        return self.do_request(request, **kwargs)


@require_GET
def list_tasks(request):
    response = []

    for task in Task.objects.all():
        response.append({"id": task.id,
                         "type": task.get_type_display(),
                         "status": task.get_status_display(),
                         "owner": task.owner,
                         "started": str(task.date_started),
                         "finished": str(task.date_finished),
                         "builddev-id": task.builddev_id,
                        })

    return JsonResponse(response, safe=False)

@require_GET
def list_images(request):
    response = []

    for img in Image.objects.all():
        rpms = []
        for rpm in img.rpms.all():
            rpms.append({"nvr": rpm.nvr,
                         "component": rpm.component,
                         })

        #registries = []
        #for reg in img.registries.all():
        #    registries.append({"url": reg.url})
        response.append({
            "hash": img.hash,
            "tags": img.tags,
            "status": img.get_status_display(),
            # "rpms": copy.copy(rpms),
            # "registries": copy.copy(registries),
            "parent": getattr(img.parent, 'hash', '')
        })

    return JsonResponse(response, safe=False)

@require_GET
def image_status(request, image_id):
    img = Image.objects.filter(hash=image_id).first()
    response = {"image_id": image_id,
                "status": img.get_status_display()}

    return JsonResponse(response)

@require_GET
def image_deps(request, image_id):
    deps = []
    for img in Image.objects.filter(base_tag=image_id).all():
        deps.append(img.hash)

    response = {"image_id": image_id,
                "deps": deps}

    return JsonResponse(response)

@require_GET
def image_info(request, image_id):
    img = Image.objects.filter(hash=image_id).first()

    rpms = []
    for rpm in img.rpms.all():
        rpms.append({"nvr": rpm.nvr,
                     "component": rpm.component,
                     })

    #registries = []
    #for reg in img.registries.all():
    #    registries.append({"url": reg.url})

    response = {"hash": img.hash,
                "status": img.get_status_display(),
                # "rpms": copy.copy(rpms),
                "tags": img.tags,
                # "registries": copy.copy(registries),
                "parent": img.parent.hash,
               }

    return JsonResponse(response, safe=False)

@require_GET
def task_status(request, task_id):
    task = Task.objects.filter(id=task_id).first()
    response = {
        "task_id": task_id,
        "status": task.get_status_display()
    }
    if hasattr(task, 'image'):
        response['image_id'] = task.image.hash
        task_data = json.loads(task.task_data.json)
        # domain = request.get_host()
        domain = socket.gethostbyname(request.META['SERVER_NAME'])
        response['message'] = "You can pull your image with command: 'dock pull %s:5000/%s'" % \
                              (domain, task_data['tag'])

    return JsonResponse(response)




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


class NewImageCall(ApiCall):
    required_args = ['git_url', 'tag']
    optional_args = ['git_dockerfile_path', 'git_commit', 'parent_registry', 'target_registries', 'repos']
    func = build

    def compose_response(self):
        return {'task_id': self.func_response}


class MoveImageCall(NewImageCall):
    required_args = ['source_registry', 'target_registry', 'tags']
    optional_args = []
    func = move_image

class RebuildImageCall(NewImageCall):
    """ rebuild provided image; use same response as new_image """
    required_args = []
    optional_args = ['git_dockerfile_path', 'git_commit', 'parent_registry',
                     'target_registries', 'repos', 'git_url', 'tag']
    func = rebuild


@require_POST
def invalidate(request, tag):
    return HttpResponse("invalidate tag {}".format(tag))
