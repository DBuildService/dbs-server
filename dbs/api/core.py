from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

import logging
from datetime import datetime

from ..models import Task, Dockerfile, Image
from ..utils import chain_dict_get


logger = logging.getLogger(__name__)


def new_image_callback(task_id, build_results):
    build_logs = getattr(build_results, 'build_logs', None)
    t = Task.objects.get(id=task_id)
    t.date_finished = datetime.now()
    if build_logs:
        t.log = '\n'.join(build_logs)
    if build_results:
        image_id = getattr(build_results, "built_img_info", {}).get("Id", None)
        logger.debug("image_id = %s", image_id)
        parent_image_id = getattr(build_results, "base_img_info", {}).get("Id", None)
        logger.debug("parent_image_id = %s", parent_image_id)
        image_tags = getattr(build_results, "built_img_info", {}).get("RepoTags", None)
        logger.debug("image_tags = %s", image_tags)
        parent_tags = getattr(build_results, "base_img_info", {}).get("RepoTags", None)
        logger.debug("parent_tags = %s", parent_tags)
        df = getattr(build_results, "dockerfile", None)
        if image_id and parent_image_id:
            parent_image = Image.create(parent_image_id, Image.STATUS_BASE, tags=parent_tags)
            image = Image.create(image_id, Image.STATUS_BUILD, tags=image_tags,
                                 task=t, parent=parent_image)
            if df:
                df_model = Dockerfile(content=df)
                df_model.save()
                image.dockerfile = df_model
                image.save()
            rpm_list = getattr(build_results, "built_img_plugins_output", {}).get("all_packages", None)
            base_rpm_list = getattr(build_results, "base_plugins_output", {}).get("all_packages", None)
            if rpm_list:
                image.add_rpms_list(rpm_list)
            if base_rpm_list:
                image.add_rpms_list(base_rpm_list)
        else:
            t.status = Task.STATUS_FAILED

        t.status = Task.STATUS_SUCCESS
    else:
        t.status = Task.STATUS_FAILED
    t.save()


def move_image_callback(task_id, response):
    logger.debug("move callback: %s %s", task_id, response)
    t = Task.objects.get(id=task_id)
    t.date_finished = datetime.now()
    if response and response.get("error", False):
        t.status = Task.STATUS_FAILED
    else:
        t.status = Task.STATUS_SUCCESS
    t.save()


