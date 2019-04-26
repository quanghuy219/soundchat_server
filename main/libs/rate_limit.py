from main.cfg import config
from main import redis


class RateLimit:
    def __init__(self, rate, duration, meta_data=None):
        """
        Inititate rate limit instance
        :param rate: maximum rate
        :param duration: time in seconds
        :param meta_data: dict
        """
        if rate < 0:
            raise ValueError('Rate cannot be less than zero')

        self.rate = rate

        if duration < 0:
            raise ValueError('Rate duration cannot be less than zero')

        self.duration = duration
        self.meta_data = meta_data

        self.key = '{}'.format(config.REDIS_PREFIX)
        for key, value in meta_data.items():
            self.key = self.key + '-{}:{}'.format(key, value)

    @property
    def is_over_limit(self):
        current_value = redis.get(self.key)
        if current_value is None:
            return False

        return int(current_value) > self.rate

    def increase(self):
        current_value = redis.get(self.key)
        if current_value is None:
            redis.set(self.key, 1, self.duration)
        else:
            redis.incr(self.key)

