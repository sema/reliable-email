
import logging

logger = logging.getLogger('reworker.LoggerBackend')
logger.setLevel(logging.DEBUG)


class LoggerBackend(object):

    def send(self, **kwargs):
        subject = kwargs['subject']
        body = kwargs['body']

        to_email = kwargs['to_email']
        to_name = kwargs.get('to_name', None)
        from_email = kwargs['from_email']
        from_name = kwargs.get('from_email', None)

        logger.info('Sending email with subject "%s" to %s %s from %s %s' %
                    (subject, unicode(to_name), to_email, unicode(from_name), from_email))

