import json
import logging
from flask import Flask, request
import redis
from requeue.requeue import DistributedQueue

DEBUG = False
LOG = None  # path to logfile

DEFAULT_FROM_EMAIL = None
DEFAULT_FROM_NAME = ''

REDIS_SERVER_URL = 'redis://localhost:6379?db=0'  # default installation

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('REFRONTEND_SETTINGS', silent=True)

# Default from email must be set!
if app.config['DEFAULT_FROM_EMAIL'] is None:
    raise RuntimeError("DEFAULT_FROM_EMAIL setting must be provided!")

# Logging
if app.config.get('LOG', None) is not None:
    file_handler = logging.FileHandler(app.config['LOG'])
    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.DEBUG)

# Connections

queue = DistributedQueue(app.config['REDIS_SERVER_URL'])


def _normalize(form, key, default=None):
    """
    Return form.get(key, default).
    However, if form[key] is the empty string then default is also used.
    """
    value = form.get(key, '').strip()
    return value if value != '' else default


@app.route('/', methods=['POST'])
def submit_email():
    """
    Accepts the following POST parameters

    subject: The subject string
    body: The email body
    to: recipient email

    to_name (optional): name of the recipient
    from (optional): sender email
    from_name (optional): name of the sender
    """

    subject = _normalize(request.form, 'subject')
    body = _normalize(request.form, 'body')

    to_email = _normalize(request.form, 'to')
    to_name = _normalize(request.form, 'to_name', None)

    from_email = _normalize(request.form, 'from', app.config['DEFAULT_FROM_EMAIL'])
    from_name = _normalize(request.form, 'from_name', app.config['DEFAULT_FROM_NAME'])

    if subject is None or body is None or to_email is None:
        message = 'Application sent malformed request missing one of arguments: subject, body or to'
        app.logger.debug(message)
        return json.dumps({'ok': False, 'error_message': message}), 400, None

    try:
        queue.push({
            'subject': subject,
            'body': body,

            'to_email': to_email,
            'to_name': to_name,

            'from_email': from_email,
            'from_name': from_name
        })

        app.logger.debug('Added email subject: %s, body: %s, to: %s' % (subject, body, to_email))
        return json.dumps({'ok': True})

    except redis.ConnectionError:
        message = 'Connection to redis refused, email rejected'
        app.logger.error(message)
        return json.dumps({'ok': False, 'error_message': message}), 500, None


if __name__ == '__main__':
    app.run()