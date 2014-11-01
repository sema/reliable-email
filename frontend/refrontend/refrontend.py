
from flask import Flask, request
from requeue import DistributedQueue

DEBUG = False

DEFAULT_FROM_EMAIL = 'no-reply@example.org'
DEFAULT_FROM_NAME = ''

# TODO move into other config file
REDIS_SERVER_URL = 'redis://localhost:6379?db=0'

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('REFRONTEND_SETTINGS', silent=True)

# TODO handle failure
queue = DistributedQueue(app.config['REDIS_SERVER_URL'])


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

    queue.push({
        'subject': request.form['subject'],
        'body': request.form['body'],

        'to_email': request.form['to'],
        'to_name': request.form.get('to_name', ''),  # optional

        'from_email': request.form.get('from', app.config['DEFAULT_FROM_EMAIL']),  # optional
        'from_name': request.form.get('from_name', app.config['DEFAULT_FROM_NAME'])  # optional
    })

    return 'OK'

if __name__ == '__main__':
    app.run(debug=True)