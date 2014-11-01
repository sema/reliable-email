
import unittest
import os

import client

TEST_SERVICE_URL = os.getenv('RE_FRONTEND_URL')

if TEST_SERVICE_URL is None:
    raise RuntimeError("RE_FRONTEND_URL environment variable must be set and point to a reliable-email web frontend!")


class TestReClient(unittest.TestCase):

    def setUp(self):
        self.client = client.ReClient(TEST_SERVICE_URL)

    def test_simple_submit(self):
        ok = self.client.submit('test email', 'body body',
                                'example@example.org')
        self.assertTrue(ok)

    def test_full_submit(self):
        ok = self.client.submit('test email', 'body body',
                                'example@example.org', 'Jane Doe',
                                'john@example.org', 'John Doe')
        self.assertTrue(ok)

    def test_invalid_submit(self):
        self.assertRaises(client.ReClientException, self.client.submit, 'test email', 'body body', '')


if __name__ == '__main__':
    unittest.main()