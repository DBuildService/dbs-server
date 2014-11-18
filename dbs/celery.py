from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement
from django.core.exceptions import ObjectDoesNotExist

import os
import logging
import time

from celery import Celery
from celery.signals import task_prerun

from django.conf import settings


logger = logging.getLogger(__name__)


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbs.settings')

app = Celery('dbs')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


@task_prerun.connect
def task_sent_handler(**kwargs):
    logger.info("kwargs = %s", kwargs)
    # broker is quicker than relational DB so this usually gets executed sooner than we have
    # celery task in DB, this suspend could solve it
    time.sleep(1)
    try:
        task_id = kwargs['task_id']
    except KeyError:
        logger.error("missing task_id in kwargs")
    else:
        from dbs.models import Task
        try:
            task = Task.objects.get(celery_id=task_id)
        except ObjectDoesNotExist:
            logger.error("No such task '%s'", task_id)
        else:
            task.state = Task.STATUS_RUNNING
            task.save()

