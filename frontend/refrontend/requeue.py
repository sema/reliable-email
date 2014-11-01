
import redis
import json


class DistributedQueue(object):

    def __init__(self, redis_url, namespace='reliableemail.queue'):
        self._redis = redis.StrictRedis.from_url(redis_url)  # According to docs redis is thread safe
        self.namespace = namespace

    def push(self, email):
        self._redis.lpush(self.namespace, json.dumps(email))

    def pop(self):
        pass

    def size(self):
        return self._redis.llen(self.namespace)

    def reset(self):
        self._redis.delete(self.namespace)