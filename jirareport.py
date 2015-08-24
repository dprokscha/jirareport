import collections
import os

import click
import pygal

import jirareport.jira
import jirareport.report


@click.group()
@click.option('--server', '-s', help='URL to JIRA server.', prompt=True, type=click.STRING)
@click.option('--username', '-u', help='Username to log into JIRA.', prompt=True, type=click.STRING)
@click.option('--password', '-p', help='Password to log into JIRA.', prompt=True, hide_input=True)
@click.pass_context
def main(ctx, server, username, password):

    jira = jirareport.jira.connect(server, username, password)

    if not jira:
        click.echo('Connection to %s failed' % server, err=True)
        exit(1)

    ctx.obj = jira


@main.command()
@click.argument('output', type=click.File('wb'))
@click.pass_context
def burndown(ctx, output=None):

    jira = ctx.obj

    board = click.prompt('Enter board ID', type=click.INT)

    click.echo('Fetching sprints: ', nl=False)

    sprints = jira.reportable_sprints(board)

    if not sprints:
        click.echo('There are no active or closed sprints for the given board ID %s.' % board)
        return

    click.echo(click.style('OK', fg='green'))

    ids = []
    for sprint in sprints:
        click.echo('ID: %s, Name: %s' % (sprint.id, sprint.name))
        ids.append(sprint.id)

    while True:
        id = click.prompt('Enter sprint ID', type=click.INT)
        if id in ids:
            break
        click.echo('Invalid sprint ID %s' % id)

    click.echo('Fetching sprint report: ', nl=False)

    sprint = jira.sprint_info(board, id)
    report = jira.sprint_report(board, id)

    if not sprint or not report or not report.all:
        click.echo('Nothing found for sprint ID %s' % id)
        return

    click.echo(click.style('OK', fg='green'))

    issues = {}

    with click.progressbar(report.all, bar_template='%(label)s [%(bar)s] %(info)s', label='Fetching issues:', show_eta=False) as all:
        for key in all:
            issues[key] = jira.issue(key, expand='changelog')

    commitment = click.prompt('Enter commitment', type=click.INT)
    burndown = jirareport.report.Burndown(sprint, commitment, report, issues)
    timeline = burndown.get_timeline()

    click.echo('Writing SVG to %s' % output.name)

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

    click.echo('Done!')


if __name__ == '__main__':
    main()