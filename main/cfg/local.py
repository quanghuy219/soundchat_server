from main.cfg.config import Config


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:minhto123@127.0.0.1:3306/soundchat_dev'
    REDIS_URI = 'redis://localhost:6379'
    REDIS_PREFIX = 'soundchat'
