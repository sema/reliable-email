
import unittest
import refrontend
from requeue.requeue import DistributedQueue


class ReliableEmailTestCase(unittest.TestCase):

    def setUp(self):
        refrontend.app.config['TESTING'] = True
        refrontend.queue.namespace += "__TESTING"  # make sure we do not hit anything bad

        self.app = refrontend.app.test_client()

    def tearDown(self):
        pass

    def test_get_disallowed(self):
        response = self.app.get('/')
        self.assertNotEqual(response.status_code, 200)

    def test_missing_args(self):
        response = self.app.post('/', data={
            'to': 'someone@example.org'
        })

        self.assertEqual(response.status_code, 400)

    def test_valid_submission_minimal(self):
        refrontend.queue.reset()

        response = self.app.post('/', data={
            'subject': 'Test',
            'body': 'Test',
            'to': 'test@example.org'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(refrontend.queue.size(), 1)

    def test_valid_submission_full(self):
        refrontend.queue.reset()

        response = self.app.post('/', data={
            'subject': 'Test',
            'body': 'Test',
            'to': 'test@example.org',
            'to_name': 'Jane Doe',
            'from': 'johndoe@example.org',
            'from_name': 'John Doe'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(refrontend.queue.size(), 1)

    def test_invalid_submission_empty_values(self):
        refrontend.queue.reset()

        response = self.app.post('/', data={
            'subject': 'Test',
            'body': 'Test',
            'to': ''
        })

        self.assertEqual(response.status_code, 400)
        self.assertEqual(refrontend.queue.size(), 0)

    def test_redis_cluster_down(self):
        old_queue = refrontend.queue
        refrontend.queue = DistributedQueue('redis://localhost:1')

        response = self.app.post('/', data={
            'subject': 'Test',
            'body': 'Test',
            'to': 'test@example.org'
        })

        refrontend.queue = old_queue
        self.assertEqual(response.status_code, 500)


if __name__ == '__main__':
    unittest.main()
