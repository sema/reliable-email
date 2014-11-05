
import redis
import json
import time


class DistributedQueueEmpty(Exception):
    def __init__(self, *args, **kwargs):
        super(DistributedQueueEmpty, self).__init__(*args, **kwargs)


class DistributedQueueException(Exception):
    def __init__(self, *args, **kwargs):
        super(DistributedQueueException, self).__init__(*args, **kwargs)


def connection_timeout_decorator(ex_class=redis.ConnectionError):
    def decorator(func):
        def wrapper(*args, **kwargs):
            connection_timeout = kwargs.pop('connection_timeout', None)
            connection_timeout_interval = kwargs.pop('connection_timeout_interval', 5)

            if connection_timeout is not None:
                deadline = time.time() + connection_timeout
                while connection_timeout == 0 or time.time() <= deadline:
                    try:
                        return func(*args, **kwargs)
                    except ex_class:
                        time.sleep(connection_timeout_interval)

            return func(*args, **kwargs)            

        return wrapper
    return decorator


class DistributedQueue(object):

    def __init__(self, redis_url, namespace='reliableemail'):
        """
        A persistent and reliable queue backed by redis.

        All calls to this queue accepts the parameters
        connection_timeout: time in seconds a call blocks if no connection can be made to redis, supply 0 for no limit (default None, no timeout)
        connection_timeout_interval: the number of seconds to wait between each retry (default 5 seconds)

        """

        self._redis = redis.StrictRedis.from_url(redis_url)  # According to docs redis is thread safe
        self.namespace = namespace

    @property
    def namespace(self):
        return self._namespace

    @namespace.setter
    def namespace(self, value):
        self._namespace = value
        self._key_queue = value + ".queue"
        self._key_processing = value + ".processing"
        self._key_discard = value + ".discard"

    @connection_timeout_decorator()
    def push(self, email):
        self._redis.lpush(self._key_queue, json.dumps(email))

    @connection_timeout_decorator()
    def reserve(self):
        """
        Pops an email from the queue for processing.
        The email is still stored in redis in case the worker dies.

        When processed call complete with the returned token to mark the email as sent.
        If the email is invalid then mark it for manual inspection by calling discard.

        If a reserved email is not handled it will eventually be moved back to the
        email queue for processing.

        :return: (email, token)
        """

        data = self._redis.rpoplpush(self._key_queue, self._key_processing)
        if data is None:
            raise DistributedQueueEmpty()

        return json.loads(data), data

    @connection_timeout_decorator()
    def complete(self, token):
        removed = self._redis.lrem(self._key_processing, 1, token)

        if removed != 1:
            raise DistributedQueueException("Token not found")

    @connection_timeout_decorator()
    def discard(self, token):
        """
        Discard a token from the processing queue to the discard queue.

        :param token:
        :return:
        """

        # Transaction start
        pipeline = self._redis.pipeline()
        pipeline.lpush(self._key_discard, token)
        pipeline.lrem(self._key_processing, 1, token)
        resp = pipeline.execute()

        if resp[1] != 1:
            # This is bad, try to remove the token from the discard list again and return
            # This can lead to some interesting inconsistency
            pipeline.lrem(self._key_discard, 1, token)

            raise DistributedQueueException("Token not found")

    @connection_timeout_decorator()
    def size(self):
        return self._redis.llen(self._key_queue)

    @connection_timeout_decorator()
    def size_processing(self):
        return self._redis.llen(self._key_processing)

    @connection_timeout_decorator()
    def size_discarded(self):
        return self._redis.llen(self._key_discard)

    @connection_timeout_decorator()
    def reset(self):
        self._redis.delete(self._key_queue)
        self._redis.delete(self._key_processing)
        self._redis.delete(self._key_discard)
