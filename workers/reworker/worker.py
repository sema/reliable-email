#!/usr/bin/env python

import click
from flanker.addresslib import address
import time
import logging

from requeue.requeue import DistributedQueue, DistributedQueueEmpty
from workers.logger import LoggerBackend
from workers.aws import AWSBackend
from workers.exceptions import WorkerInvalidEmail

workers = {
    'logger': LoggerBackend,
    'aws': AWSBackend
}

logger = logging.getLogger('reworker')
logger.addHandler(logging.NullHandler())  # hide errors about missing handlers


def _validate_email(email):
    """
    Validate well-formness of email

    E.g. that subject and body are non-empty, and to and from email addresses are valid.

    :return: valid, reason where valid is a boolean and reason is a string
    """

    # TODO This should be more defensive. What if subject and body are not strings?
    # We could also return better error messages.

    # 1. subject and body are non-empty
    if email.get('subject', '').strip() == '':
        return False, 'Subject is empty'
    if email.get('body', '').strip() == '':
        return False, 'Body is empty'

    # 2. to_email and from_email are valid e-mails
    # We use mailgun's flanker (https://github.com/mailgun/flanker) for the heavy lifting
    email['to_email'] = address.parse(email.get('to_email', ''), addr_spec_only=True)
    email['from_email'] = address.parse(email.get('from_email', ''), addr_spec_only=True)  # TODO cache this check?

    if email['to_email'] is None:
        return False, 'To-Email is not valid'

    if email['from_email'] is None:
        return False, 'From-Email is not valid'

    return True, ''


def run(worker, queue, terminate_after_one_iteration=False, wait_on_empty=5, connection_timeout=0):

    while 1:
        try:
            email, token = queue.reserve(connection_timeout=connection_timeout)
            valid, reason = _validate_email(email)

            if valid:

                try:
                    email['connection_timeout'] = connection_timeout  # pass connection timeout settings to worker
                    worker.send(**email)
                except WorkerInvalidEmail:
                    queue.discard(token, connection_timeout=connection_timeout)
                else:
                    queue.complete(token, connection_timeout=connection_timeout)

            else:
                queue.discard(token, connection_timeout=connection_timeout)

        except DistributedQueueEmpty:
            time.sleep(wait_on_empty)
        except Exception:
            # This should never happen, log the error and stop running so we can restart (let the exception bubble up)
            logger.exception('An exception occurred when processing emails')
            raise

        if terminate_after_one_iteration:
            break


@click.group()
def cli():
    pass


@cli.command()
@click.option('--redis-url', default=None, help='Redis cluster used to persist email queue.')
@click.option('--log', default=None, help='Path to log file')
@click.option('--verbose', default=False, is_flag=True)
@click.argument('backend')
@click.pass_context
def start(ctx, redis_url, log, verbose, backend):
    if redis_url is None:
        redis_url = 'redis://localhost:6379?db=0'

    if log is not None:
        handler = logging.FileHandler(log)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    if verbose:
        handler = logging.StreamHandler(click.get_text_stream('stdout'))
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    worker = workers.get(backend, None)

    if worker is None:
        ctx.fail('Unknown backend: %s' % backend)

    click.echo('Starting worker using backend: %s' % backend)

    queue = DistributedQueue(redis_url)
    run(worker(), queue)


@cli.command()
def available():
    for key in workers.keys():
        click.echo(key)

if __name__ == '__main__':
    cli()
