import collections
import os

import click

import app.jira


def load_commands(f):

    app_path = os.path.dirname(os.path.realpath(__file__))
    commands_path = os.path.join(app_path, 'app', 'commands')

    for filename in os.listdir(commands_path):
        if not filename.endswith('.py'):
            continue

        name = os.path.splitext(filename)[0]
        module = __import__('app.commands.%s' % name,
                            fromlist=['app.commands'])
        command = getattr(module, name)
        f.add_command(command)

    return f


@load_commands
@click.group()
@click.option('--server', '-s',
              help='URL to JIRA server.',
              prompt=True,
              type=click.STRING)
@click.option('--username', '-u',
              help='Username to log into JIRA.',
              prompt=True,
              type=click.STRING)
@click.option('--password', '-p',
              help='Password to log into JIRA.',
              prompt=True,
              hide_input=True)
@click.option('--customfield', '-c',
              help='JIRA internal field name for issue estimation.',
              prompt=True,
              type=click.STRING)
@click.pass_context
def main(ctx, server, username, password, customfield):

    jira = app.jira.connect(server, username, password)
    if not jira:
        click.echo('Connection to {0} failed'.format(server), err=True)
        exit(1)

    Session = collections.namedtuple('Session', 'jira customfield')
    ctx.obj = Session(jira=jira, customfield=customfield)


if __name__ == '__main__':
    main()
