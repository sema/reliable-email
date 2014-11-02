
import os
import logging
import boto.ses
from boto.ses.exceptions import SESDailyQuotaExceededError, SESMaxSendingRateExceededError, SESError
from boto.exception import StandardError

from exceptions import WorkerTemporaryError, WorkerInvalidEmail, WorkerRemoteError
from requeue.requeue import connection_timeout_decorator

logger = logging.getLogger('reworker.AWSBackend')
logger.setLevel(logging.DEBUG)


class AWSBackend(object):

    def __init__(self):
        aws_key = os.getenv('AWS_KEY')
        if aws_key is None:
            raise RuntimeError("AWS_KEY environment variable must be set to your AWS key id!")

        aws_secret = os.getenv('AWS_SECRET')
        if aws_secret is None:
            raise RuntimeError("AWS_SECRET environment variable must be set to your AWS secret key!")

        self.conn = boto.ses.connect_to_region(
            'us-east-1',
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret)

    @connection_timeout_decorator((WorkerTemporaryError, WorkerRemoteError))
    def send(self, **kwargs):

        subject = kwargs['subject']
        body = kwargs['body']

        to_email = kwargs['to_email']
        to_name = kwargs.get('to_name', None)
        from_email = kwargs['from_email']
        from_name = kwargs.get('from_email', None)

        logger.info('Sending email with subject "%s" to %s %s from %s %s' %
                    (subject, unicode(to_name), to_email, unicode(from_name), from_email))

        try:
            self.conn.send_email(
                from_email,
                subject,
                body,
                [to_email]
            )

        except SESDailyQuotaExceededError:
            message = 'SES daily quota exceeded'
            logger.exception(message)
            raise WorkerTemporaryError(message)

        except SESMaxSendingRateExceededError:
            message = 'SES sending rate exceeded'
            logger.exception(message)
            raise WorkerTemporaryError(message)

        except SESError, ex:
            # Invalid input, reject
            message = 'Invalid email given to worker: %s' % ex.reason
            logger.exception(message)
            raise WorkerInvalidEmail(message)

        except StandardError, ex:
            # Connection error
            message = 'Fatal error from AWS: %s' % ex.reason
            logger.exception(message)
            raise WorkerRemoteError(message)
