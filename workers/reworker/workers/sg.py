
import os
import logging
from sendgrid import SendGridClient, SendGridClientError, SendGridServerError, Mail

from exceptions import WorkerTemporaryError, WorkerInvalidEmail, WorkerRemoteError
from requeue.requeue import connection_timeout_decorator

logger = logging.getLogger('reworker.SendgridBackend')
logger.setLevel(logging.DEBUG)


class SendgridBackend(object):

    def __init__(self):
        sendgrid_username = os.getenv('SENDGRID_USERNAME')
        if sendgrid_username is None:
            raise RuntimeError("SENDGRID_USERNAME environment variable must be set to your Sendgrid username!")

        sendgrid_password = os.getenv('SENDGRID_PASSWORD')
        if sendgrid_password is None:
            raise RuntimeError("SENDGRID_PASSWORD environment variable must be set to your Sendgrid password!")

        self.client = SendGridClient(sendgrid_username, sendgrid_password, raise_errors=True)

    @connection_timeout_decorator((WorkerTemporaryError, WorkerRemoteError))
    def send(self, **kwargs):

        subject = kwargs['subject']
        body = kwargs['body']

        to_email = kwargs['to_email']
        to_name = kwargs.get('to_name', '')
        from_email = kwargs['from_email']
        from_name = kwargs.get('from_email', '')

        logger.info('Sending email with subject "%s" to %s %s from %s %s' %
                    (subject, unicode(to_name), to_email, unicode(from_name), from_email))

        try:
            mail = Mail(subject=subject, html=body,
                        to=[to_email], to_name=[to_name],
                        from_email=from_email, from_name=from_name)

            self.client.send(mail)

        except SendGridServerError, ex:
            message = 'Sendgrid server error: %s' % ex.message
            logger.exception(message)
            raise WorkerRemoteError(message)

        except SendGridClientError, ex:
            # Invalid input? This could also be raised because of an error in our configuration...
            # TODO Add another exception which allows a client to back down in this case
            message = 'Sendgrid client error: %s' % ex.message
            logger.exception(message)
            raise WorkerInvalidEmail(message)

