from threading import Thread
from celery import Celery

from . import tasks
from .celery import app

__all__ = ('TaskApi', )


def watch_task(task, callback, kwargs=None):
    """
    watch task until it ends and then execute callback:

        callback(response, **kwargs)

    where response is a result of task

    :param task: task to watch
    :param callback: function which is called when task finishes
    :param kwargs: dict which is passed to callback

    :return: None
    """
    response = task.wait()
    if kwargs:
        callback(response, **kwargs)
    else:
        callback(response)


class TaskApi(object):
    """ universal API for tasks which are executed on celery workers """

    def build_docker_image(self, build_image, git_url, local_tag, git_dockerfile_path=None, git_commit=None,
                           parent_registry=None, target_registries=None, tag=None, repos=None,
                           callback=None, kwargs=None):
        """
        build docker image from supplied git repo

        TODO:
        DockerFile has to be in root of the gitrepo, path and commit are not implemented yet
        yum repos

        :param build_image: name of the build image (supplied docker image is built inside this image)
        :param git_url: url to git repo
        :param local_tag: image is known within the service with this tag
        :param git_dockerfile_path: path to dockerfile within git repo (default is ./Dockerfile)
        :param git_commit: which commit to checkout (master by default)
        :param parent_registry: pull base image from this registry
        :param target_registries: list of urls where built image will be pushed
        :param tag: tag image with this tag (and push it to target_repo if specified)
        :param repos: list of yum repos to enable in image
        :param callback: function to call when task finishes, it has to accept at least
                        one argument: return value of task
        :param kwargs: dict which is pass to callback, callback is called like this:
                         callback(task_response, **kwargs)
        :return: task_id
        """
        args = (build_image, git_url, local_tag)
        task_kwargs = {'parent_registry': parent_registry,
                       'target_registries': target_registries,
                       'tag': tag,
                       'git_commit': git_commit,
                       'git_dockerfile_path': git_dockerfile_path,
                       'repos': repos}
        task_info = tasks.build_image.apply_async(args=args, kwargs=task_kwargs,
                                                   link=tasks.submit_results.s())
        task_id = task_info.task_id
        if callback:
            t = Thread(target=watch_task, args=(task_info, callback, kwargs))
            #w.daemon = True
            t.start()
        return task_id

    def find_dockerfiles_in_git(self):
        raise NotImplemented()

    def push_docker_image(self, image_id, source_registry, target_registry, tags, callback=None, kwargs=None):
        """
        pull docker image from source registry, tag it with multiple tags and push it to target registry

        :param image_id: image to pull
        :param source_registry: registry to pull from
        :param target_registry: registry for pushing
        :param tags: list of tags for image tagging
        :param callback: function to call when task finishes, it has to accept at least
                        one argument: return value of task
        :param kwargs: dict which is pass to callback, callback is called like this:
                         callback(task_response, **kwargs)
        :return: task_id
        """
        task_info = tasks.push_image.delay(image_id, source_registry, target_registry, tags)
        task_id = task_info.task_id
        if callback:
            t = Thread(target=watch_task, args=(task_info, callback, kwargs))
            #w.daemon = True
            t.start()
        return task_id


def desktop_callback(data):
    """ show desktop notification when build finishes """
    from pprint import pprint
    pprint(data)
    try:
        from gi.repository import Notify
    except ImportError:
        pass
    else:
        Notify.init("Docker Build Service")
        n = Notify.Notification.new(
            "Docker Build Service",
            "Docker Build of '%s' has finished." % data[0]['Id'],
            "dialog-information"
        )
        n.show()

if __name__ == '__main__':
    t = TaskApi()
    t.build_docker_image(build_image="buildroot-fedora",
                         git_url="github.com/TomasTomecek/docker-hello-world.git",
                         local_tag="fedora-celery-build",
                         callback=desktop_callback)

