class Config(object):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'super_secret_key'
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@127.0.0.1:3306/soundchat_dev'
    REDIS_URI = 'redis://localhost:6379/5'
    REDIS_PREFIX = 'soundchat'
    PUSHER_APP_ID = '750022'
    PUSHER_KEY = '8ca50ca8ff937987bdce'
    PUSHER_SECRET = '27255f4589e44be0e6e4'
    PUSHER_CLUSTER = 'ap1'
    PUSHER_SSL = True
    PUSHER_NAMESPACE = ''
    CELERY_BROKER = 'redis://localhost:6379/5'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://utphot2sfcfemrxl:vx0cItbYZDej5BZblmwB@bteo6uriyjlc0sfz750r-mysql.services.clever-cloud.com:3306/bteo6uriyjlc0sfz750r'
