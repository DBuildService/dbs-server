from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

import json
import logging

from django.http import JsonResponse
from django.views.generic import View

from .core import (
    build, rebuild, ErrorDuringRequest,
    move_image, invalidate, task_status, image_info,
    list_images, image_status, image_deps, list_tasks
)
from ..task_api import TaskApi


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
        logger.debug("request: %s", kwargs)
        kwargs['request'] = request
        self.process(**kwargs)
        if self.error_response:
            return JsonResponse(self.error_response)
        return JsonResponse(self.compose_response(), safe=False)

    def post(self, request, **kwargs):
        self.args = self.validate_rest_input()
        return self.do_request(request, **kwargs)

    def get(self, request, **kwargs):
        return self.do_request(request, **kwargs)


class ImageStatusCall(ApiCall):
    func = image_status


class ImageInfoCall(ApiCall):
    func = image_info


class ImageDepsCall(ApiCall):
    func = image_deps

class ListImagesCall(ApiCall):
    func = list_images


class TaskStatusCall(ApiCall):
    func = task_status


class ListTasksCall(ApiCall):
    func = list_tasks


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


class InvalidateImageCall(ApiCall):
    required_args = []
    optional_args = []
    func = invalidate

    def compose_response(self):
        return {'message': "Invalidated %d images." % self.func_response}
