import collections

import click
import pygal

import jirareport.ask
import jirareport.filter
import jirareport.jira
import jirareport.report


@click.group()
@click.option('--server', '-s', help='URL to JIRA server.', prompt=True, type=click.STRING)
@click.option('--username', '-u', help='Username to log into JIRA.', prompt=True, type=click.STRING)
@click.option('--password', '-p', help='Password to log into JIRA.', prompt=True, hide_input=True)
@click.option('--customfield', '-c', help='JIRA internal field name for issue estimation.', prompt=True, type=click.STRING)
@click.pass_context
def main(ctx, server, username, password, customfield):

    jira = jirareport.jira.connect(server, username, password)

    if not jira:
        click.echo('Connection to {0} failed'.format(server), err=True)
        exit(1)

    obj = collections.namedtuple('Context', 'jira customfield')
    ctx.obj = obj(jira=jira, customfield=customfield)


@main.command()
@click.argument('output', type=click.File('wb'))
@click.pass_context
def burndown(ctx, output=None):

    jira = ctx.obj.jira
    customfield = ctx.obj.customfield

    try:
        board, sprints = jirareport.ask.for_board(jira)
        id = jirareport.ask.for_sprint(jira, board, sprints)

    except Exception as e:
        click.secho(str(e), fg='red')
        exit(1)

    click.echo('Fetching sprint report: ', nl=False)

    sprint = jira.sprint_info(board, id)
    report = jira.sprint_report(board, id)

    if not sprint or not report or not report.all:
        click.secho('Nothing found for sprint ID {0}'.format(id), fg='red')
        exit(1)

    click.secho('OK', fg='green')

    labels = jirareport.ask.for_labels()
    issues, report = jirareport.filter.for_labels(jira, report, labels)

    commitment = click.prompt('Enter commitment', type=click.INT)
    burndown = jirareport.report.Burndown(sprint, commitment, report, issues, customfield)
    timeline = burndown.get_timeline()
    velocity = commitment - timeline['completed'][-1]

    for key, message in burndown.faulty.items():
        click.echo('{0} is faulty: {1}'.format(key, message))

    if 'CLOSED' == sprint['state']:
        click.echo('Velocity: {0}'.format(velocity))

    click.echo('Writing SVG to {0}'.format(output.name))

    style = pygal.style.Style(
        background='transparent',
        colors=('#b4b4b4', '#00b400', '#b40000'),
        foreground='#000000',
        foreground_strong='#000000',
        foreground_subtle='#000000',
        plot_background='transparent',
    )

    chart = pygal.Line(
        interpolate='cubic',
        style=style,
        x_label_rotation=90
    )
    chart.title = 'Burndown, {0}'.format(sprint['name'])
    chart.x_title = 'Dates'
    chart.x_labels = timeline['dates']
    chart.y_title = 'Story Points'
    chart.add('Ideal', timeline['ideal'])
    chart.add('Completed', timeline['completed'])
    chart.add('Unplanned', timeline['unplanned'])
    chart.value_formatter = lambda x: "%d" % x
    output.write(chart.render())

    click.echo('Done!')


@main.command()
@click.pass_context
def dailybusiness(ctx):

    jira = ctx.obj.jira

    key = click.prompt('Enter issue key', type=click.STRING)

    try:
        issue = jira.issue(key)

    except Exception:
        click.echo('Issue not found: {0}'.format(key), err=True)
        exit(1)

    length = 0
    while length <= 0:
        length = click.prompt('Enter sprint length', type=click.INT)

        if length <= 0:
            click.echo('Error: Invalid sprint length')

    dailybusiness = jirareport.report.dailybusiness.analyse(issue.fields.comment.comments)
    average = jirareport.report.dailybusiness.average(length, dailybusiness['hours'], dailybusiness['minutes'])

    click.echo('Found {0}h {1}m of daily business. Average per day: {2}h {3}m'.format(dailybusiness['hours'],
                                                                                      dailybusiness['minutes'],
                                                                                      average['hours'],
                                                                                      average['minutes']))

    click.echo('Done!')


if __name__ == '__main__':
    main()