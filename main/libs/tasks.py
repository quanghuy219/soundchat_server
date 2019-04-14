from __future__ import absolute_import, unicode_literals

from celery import Celery

from main.cfg import config

celery_app = Celery('TaskQueue',
                    broker=config.CELERY_BROKER)



