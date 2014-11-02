
class LoggerBackend(object):

    def send(self, **kwargs):
        subject = kwargs['subject']
        body = kwargs['body']

        to_email = kwargs['to_email']
        to_name = kwargs.get('to_name', None)
        from_email = kwargs['from_email']
        from_name = kwargs.get('from_email', None)

        pass
