#!/usr/bin/env python

import click
from requeue.requeue import DistributedQueue


@click.group()
@click.option('--redis-url', default=None, help='Redis cluster used to persist email queue.')
@click.pass_context
def cli(ctx, redis_url):
    if redis_url is None:
        redis_url = 'redis://localhost:6379?db=0'

    ctx.obj = DistributedQueue(redis_url)


@cli.command()
@click.pass_context
def size(ctx):
    click.echo(ctx.obj.size())


@cli.command()
@click.pass_context
def clear(ctx):
    if click.confirm('Are you sure you want to clear the queue (data will be lost)?'):
        ctx.obj.reset()
        click.echo("Queue cleared.")


if __name__ == '__main__':
    cli()
