
from flask import Flask, request, render_template, flash, redirect, url_for
from reclient.client import ReClient, ReClientException
import os
import logging

DEBUG = False
SECRET_KEY = 'CHANGE ME'

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('REWEBCLIENT_SETTINGS', silent=True)

app.config['RE_FRONTEND_URL'] = app.config.get('RE_FRONTEND_URL', None)
if app.config['RE_FRONTEND_URL'] is None:
    app.config['RE_FRONTEND_URL'] = os.getenv('RE_FRONTEND_URL')
if app.config['RE_FRONTEND_URL'] is None:
    raise RuntimeError("RE_FRONTEND_URL environment variable must be set and point to a reliable-email web frontend!")

# Logging
if app.config.get('LOG', None) is not None:
    file_handler = logging.FileHandler(app.config['LOG'])
    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.DEBUG)

client = ReClient(app.config['RE_FRONTEND_URL'])


@app.route('/', methods=['GET', 'POST'])
def index():

    # We could use something like WTForms here, but I'll just keep it simple.
    # I'm ignoring all kinds of i'llformed user input, and let the web frontend handle the small amount of validation

    if request.method == 'POST':
        try:
            client.submit(
                request.form.get('subject', ''),
                request.form.get('body', ''),
                request.form.get('to_email', ''),
                request.form.get('to_name', '')
            )

            flash(u'Frontend returned a OK, job submitted!')

        except ReClientException, ex:
            flash(u'Job failed submission: %s' % ex.message)

        redirect(url_for('index'))

    return render_template('index.html')


if __name__ == '__main__':
    app.run()
