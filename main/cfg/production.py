from main.cfg.config import Config


class ProductionConfig(Config):
    PUSHER_APP_ID = "750024"
    PUSHER_KEY = "212af40d49e82f344e49"
    PUSHER_SECRET = "2ed0217dd314e94946f9"
    PUSHER_CLUSTER = "ap1"
    PUSHER_NAMESPACE = 'soundchat'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://admin:admin@321@soundchat-mysql:3306/soundchat_dev?charset=utf8mb4'
    CELERY_BROKER = 'redis://soundchat-redis'
    REDIS_URI = 'redis://soundchat-redis'
