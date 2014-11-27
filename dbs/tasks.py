from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

import logging

from celery import shared_task
from dock.core import DockerTasker
from dock.api import build_image_in_privileged_container, build_image_using_hosts_docker


logger = logging.getLogger(__name__)


@shared_task
def build_image_hostdocker(
        build_image, git_url, local_tag, git_dockerfile_path=None,
        git_commit=None, parent_registry=None, target_registries=None,
        tag=None, repos=None, store_results=True):
    """
    build docker image, image is built inside container using docker instance
    from host (mount socket inside container)

    :param build_image: name of the build image (supplied docker image is built inside this image)
    :param git_url: url to git repo
    :param local_tag: image is known within the service with this tag
    :param git_dockerfile_path: path to dockerfile within git repo (default is ./Dockerfile)
    :param git_commit: which commit to checkout (master by default)
    :param parent_registry: pull base image from this registry
    :param target_registries: list of urls where built image will be pushed
    :param tag: tag image with this tag (and push it to target_repo if specified)
    :param repos: list of yum repos to enable in image
    :param store_results: if set to True, store built image and associated buildroot
                          in local docker registry
    :return: dict with data from docker inspect
    """
    logger.info("build image using hostdocker method")
    target_registries = target_registries or []
    push_buildroot_to = None
    if store_results:
        target_registries.append('172.17.42.1:5000')
        push_buildroot_to = "172.17.42.1:5000"
    results = build_image_using_hosts_docker(
        build_image,
        git_url=git_url,
        image=local_tag,
        git_dockerfile_path=git_dockerfile_path,
        git_commit=git_commit,
        parent_registry=parent_registry,
        target_registries=target_registries,
        repos=repos,
        push_buildroot_to=push_buildroot_to,
    )
    return results

@shared_task
def build_image(build_image, git_url, local_tag, git_dockerfile_path=None,
                git_commit=None, parent_registry=None, target_registries=None,
                tag=None, repos=None, store_results=True):
    """
    build docker image from provided arguments inside privileged container

    :param build_image: name of the build image (supplied docker image is built inside this image)
    :param git_url: url to git repo
    :param local_tag: image is known within the service with this tag
    :param git_dockerfile_path: path to dockerfile within git repo (default is ./Dockerfile)
    :param git_commit: which commit to checkout (master by default)
    :param parent_registry: pull base image from this registry
    :param target_registries: list of urls where built image will be pushed
    :param tag: tag image with this tag (and push it to target_repo if specified)
    :param repos: list of yum repos to enable in image
    :param store_results: if set to True, store built image and associated buildroot
                          in local docker registry
    :return: dict with data from docker inspect
    """
    logger.info("build image in privileged container")
    target_registries = target_registries or []
    push_buildroot_to = None
    if store_results:
        target_registries.append('172.17.42.1:5000')
        push_buildroot_to = "172.17.42.1:5000"
    results = build_image_in_privileged_container(
        build_image,
        git_url=git_url,
        image=local_tag,
        git_dockerfile_path=git_dockerfile_path,
        git_commit=git_commit,
        parent_registry=parent_registry,
        target_registries=target_registries,
        repos=repos,
        push_buildroot_to=push_buildroot_to,
    )
    return results


@shared_task
def push_image(image_id, source_registry, target_registry, tags):
    """
    pull image from source_registry and push it to target_registry (with provided tags)

    :param image_id: image to pull
    :param source_registry: registry to pull image from
    :param target_registry: registry to push image to
    :param tags: list of tags to tag image with before pushing it to target registry
    :return: None
    """
    if not hasattr(tags, '__iter__'):
        raise RuntimeError("argument tags is not iterable")
    d = DockerTasker()
    try:
        final_tag = d.pull_image(image_id, source_registry)
        for tag in tags:
            d.tag_and_push_image(final_tag, tag, reg_uri=target_registry)
    except Exception as ex:
        return {"error": repr(ex.message)}
    else:
        return {"error": None}


@shared_task
def submit_results(result):
    """
    TODO: implement this
    """
    # 2 requests, one for 'finished', other for data
    print(result)

