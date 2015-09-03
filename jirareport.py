import collections

import click
import pygal

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
        click.echo('Connection to %s failed' % server, err=True)
        exit(1)

    obj = collections.namedtuple('Context', 'jira customfield')
    ctx.obj = obj(jira=jira, customfield=customfield)


@main.command()
@click.argument('output', type=click.File('wb'))
@click.pass_context
def burndown(ctx, output=None):

    jira = ctx.obj.jira
    customfield = ctx.obj.customfield

    board = click.prompt('Enter board ID', type=click.INT)

    click.echo('Verifying board ID: ', nl=False)

    try:
        reportable = jira.reportable_sprints(board)

    except Exception:
        reportable = None

    if not reportable:
        click.echo('There are no active or closed sprints for the given board ID %s.' % board)
        return

    click.secho('OK', fg='green')

    details = []
    with click.progressbar(reportable, bar_template='%(label)s [%(bar)s] %(info)s', label='Fetching sprints:', show_eta=False) as sprints:
        for sprint in sprints:
            details.append(jira.get_sprint(board, sprint.id))

    details.sort(key=lambda sprint: sprint['startDate'])

    for sprint in details:
        click.echo('ID %s, Created: %s, Name: %s' % (sprint['id'], sprint['startDate'].strftime('%Y-%m-%d'), sprint['name']))

    while True:
        id = click.prompt('Enter sprint ID', type=click.INT)
        if any(sprint['id'] == id for sprint in details):
            break
        click.echo('Invalid sprint ID %s' % id)

    click.echo('Fetching sprint report: ', nl=False)

    sprint = jira.sprint_info(board, id)
    report = jira.sprint_report(board, id)

    if not sprint or not report or not report.all:
        click.echo('Nothing found for sprint ID %s' % id)
        return

    click.secho('OK', fg='green')

    labels = []
    if click.confirm('Filter issues for labels?'):
        while True:
            try:
                labels.append(click.prompt('Enter label (interrupt to leave)', type=click.STRING))
            except Exception:
                break

    issues = {}
    ignored = []
    with click.progressbar(report.all, bar_template='%(label)s [%(bar)s] %(info)s', label='Fetching issues:', show_eta=False) as all:
        for key in all:

            issue = jira.issue(key, expand='changelog')

            if labels and not [label for label in labels if label in issue.fields.labels]:
                ignored.append(key)
                continue

            issues[key] = issue

    for key in ignored:
        if key in report.completed:
            report.completed.remove(key)
        if key in report.incompleted:
            report.incompleted.remove(key)
        if key in report.added:
            report.added.remove(key)
        if key in report.punted:
            report.punted.remove(key)
        if key in report.all:
            report.all.remove(key)

    commitment = click.prompt('Enter commitment', type=click.INT)
    burndown = jirareport.report.Burndown(sprint, commitment, report, issues, customfield)
    timeline = burndown.get_timeline()
    velocity = commitment - timeline['completed'][-1]

    click.echo('Velocity: %s ' % velocity)
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


@main.command()
@click.pass_context
def dailybusiness(ctx):

    jira = ctx.obj.jira

    key = click.prompt('Enter issue key', type=click.STRING)

    try:
        issue = jira.issue(key)

    except Exception:
        click.echo('Issue not found: %s' % key, err=True)
        exit(1)

    length = 0
    while length <= 0:
        length = click.prompt('Enter sprint length', type=click.INT)

        if length <= 0:
            click.echo('Error: Invalid sprint length')

    dailybusiness = jirareport.report.dailybusiness.analyse(issue.fields.comment.comments)
    average = jirareport.report.dailybusiness.average(length, dailybusiness['hours'], dailybusiness['minutes'])

    click.echo('Found %dh %dm of daily business. Average per day: %dh %dm' % (dailybusiness['hours'],
                                                                              dailybusiness['minutes'],
                                                                              average['hours'],
                                                                              average['minutes']))

    click.echo('Done!')


if __name__ == '__main__':
    main()