import os

from main.cfg.local import DevelopmentConfig
from main.cfg.production import ProductionConfig
from main.cfg.test import TestingConfig

configs = {
    'production': ProductionConfig,
    'development': DevelopmentConfig,
    'test': TestingConfig
}

config = configs.get(os.getenv('FLASK_ENV', 'development'))()
