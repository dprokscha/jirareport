import collections
import os

import click
import pygal

import jirareport.jira
import jirareport.report


def path():
    return os.path.dirname(os.path.realpath(__file__))


@click.group()
@click.option('--server', '-s', help='URL to JIRA server.', prompt=True, type=click.STRING)
@click.option('--username', '-u', help='Username to log into JIRA.', prompt=True, type=click.STRING)
@click.option('--password', '-p', help='Password to log into JIRA.', prompt=True, hide_input=True)
@click.option('--board', '-b', help='JIRA board ID to read the sprints from.', prompt=True, type=click.INT)
@click.option('--ignore_sprint', '-i', help='Sprint ID which is ignored for the reports.', multiple=True, type=click.INT)
@click.pass_context
def main(ctx, server, username, password, board, ignore_sprint):

    jira = jirareport.jira.connect(server, username, password)

    if not jira:
        print('Connection to %s failed' % server)
        exit(1)

    obj = collections.namedtuple('Shared', 'jira board ignore_sprint')
    ctx.obj = obj(jira=jira, board=board, ignore_sprint=ignore_sprint)


@main.command()
@click.argument('output', type=click.File('wb'))
@click.pass_context
def burndown(ctx, output=None):

    print('Fetching sprints: ', end='', flush=True)

    jira = ctx.obj.jira
    board = ctx.obj.board
    ignore_sprint = ctx.obj.ignore_sprint

    sprints = jira.reportable_sprints(board, ignore_sprint)

    if not sprints:
        print('There are no active or closed sprints for the given board ID %s.' % board)
        return

    print('OK')

    ids = []
    for sprint in sprints:
        print('ID: %s, Name: %s' % (sprint.id, sprint.name))
        ids.append(sprint.id)

    while True:
        id = click.prompt('Enter sprint ID', type=click.INT)
        if id in ids:
            break
        print('Invalid sprint ID %s' % id)

    print('Fetching sprint report: ', end='', flush=True)

    sprint = jira.sprint_info(board, id)
    report = jira.sprint_report(board, id)

    if not sprint or not report or not report.all:
        print('Nothing found for sprint ID %s' % id)
        return

    print('OK')

    issues = {}

    with click.progressbar(report.all, bar_template='%(label)s [%(bar)s] %(info)s', label='Fetching issues:', show_eta=False) as all:
        for key in all:
            issues[key] = jira.issue(key, expand='changelog')

    commitment = click.prompt('Enter commitment', type=click.INT)
    burndown = jirareport.report.Burndown(sprint, commitment, report, issues)
    timeline = burndown.get_timeline()

    print('Writing SVG to %s' % output.name)

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
    chart.title = 'Burndown, %s' % sprint['name']
    chart.x_title = 'Dates'
    chart.x_labels = timeline['dates']
    chart.y_title = 'Story Points'
    chart.add('Ideal', timeline['ideal'])
    chart.add('Completed', timeline['completed'])
    chart.add('Unplanned', timeline['unplanned'])
    chart.value_formatter = lambda x: "%d" % x
    output.write(chart.render())

    print('Done')


if __name__ == '__main__':
    main()