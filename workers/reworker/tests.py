
import os
import unittest
import logging

import redis
from requeue.requeue import DistributedQueue

import worker
from workers.logger import LoggerBackend

RE_REDIS_URL = os.getenv('RE_REDIS_URL')
if RE_REDIS_URL is None:
    raise RuntimeError("RE_REDIS_URL environment variable must be set and point to the reliable-email redis cluster!")

_asset_dummy_email = {
    'subject': 'Test email',
    'body': 'test test',
    'to_email': 'example@example.org',
    'from_email': 'example@example.org'
}

_asset_invalid_email_dummy_email = {
    'subject': 'Test email',
    'body': 'test test',
    'to_email': 'example@eample',
    'from_email': 'example'
}

_asset_invalid_subject_dummy_email = {
    'body': 'test test',
    'to_email': 'example@example.org',
    'from_email': 'example@example.org'
}


class AlwaysWorkingWorkerMock(object):
    def __init__(self):
        self.send_count = 0

    def send(self, **kwargs):
        self.send_count += 1


class ReWorkerTest(unittest.TestCase):

    def setUp(self):
        self.queue = DistributedQueue(RE_REDIS_URL)
        self.queue.namespace += "__TESTING"  # make sure we do not hit anything bad

    def test_iteration_expected_path(self):
        self.queue.reset()
        self.queue.push(_asset_dummy_email)

        w = AlwaysWorkingWorkerMock()
        worker.run(w, self.queue, True)

        self.assertEqual(w.send_count, 1)
        self.assertEqual(self.queue.size(), 0)
        self.assertEqual(self.queue.size_processing(), 0)
        self.assertEqual(self.queue.size_discarded(), 0)

    def test_iteration_empty_queue(self):
        self.queue.reset()

        w = AlwaysWorkingWorkerMock()
        worker.run(w, self.queue, True, wait_on_empty=0)

        self.assertEqual(w.send_count, 0)
        self.assertEqual(self.queue.size(), 0)
        self.assertEqual(self.queue.size_processing(), 0)
        self.assertEqual(self.queue.size_discarded(), 0)

    def test_iteration_invalid_email(self):
        self.queue.reset()
        self.queue.push(_asset_invalid_email_dummy_email)

        w = AlwaysWorkingWorkerMock()
        worker.run(w, self.queue, True, wait_on_empty=0)

        self.assertEqual(w.send_count, 0)
        self.assertEqual(self.queue.size(), 0)
        self.assertEqual(self.queue.size_processing(), 0)
        self.assertEqual(self.queue.size_discarded(), 1)

    def test_iteration_missing_subject(self):
        self.queue.reset()
        self.queue.push(_asset_invalid_subject_dummy_email)

        w = AlwaysWorkingWorkerMock()
        worker.run(w, self.queue, True, wait_on_empty=0)

        self.assertEqual(w.send_count, 0)
        self.assertEqual(self.queue.size(), 0)
        self.assertEqual(self.queue.size_processing(), 0)
        self.assertEqual(self.queue.size_discarded(), 1)

    def test_cant_connect_to_redis(self):
        w = AlwaysWorkingWorkerMock()
        queue = DistributedQueue('redis://localhost:1')

        self.assertRaises(redis.ConnectionError, worker.run, w, queue, True, connection_timeout=None)
        self.assertEqual(w.send_count, 0)


class LoggerTest(unittest.TestCase):

    def setUp(self):
        self.queue = DistributedQueue(RE_REDIS_URL)
        self.queue.namespace += "__TESTING"  # make sure we do not hit anything bad

    def test_expected_path(self):
        # Test if the logger adds something to the log

        class DummyHandler(logging.NullHandler):
            def __init__(self):
                self.logcount = 0

            def handle(self, *args, **kwargs):
                self.logcount += 1

        logger = logging.getLogger('reworker.LoggerBackend')

        handler = DummyHandler()
        handler.setLevel(logging.DEBUG)

        logger.addHandler(handler)

        # Trigger the logger

        self.queue.reset()
        self.queue.push(_asset_dummy_email)

        w = LoggerBackend()
        worker.run(w, self.queue, True)
        self.assertEqual(handler.logcount, 1)


if __name__ == '__main__':
    unittest.main()