from __future__ import absolute_import, unicode_literals

from celery import Celery

from main.cfg import config

celery_app = Celery('TaskQueue',
                    broker=config.CELERY_BROKER)
celery_app.conf.broker_transport_options = {'visibility_timeout': 10800}
