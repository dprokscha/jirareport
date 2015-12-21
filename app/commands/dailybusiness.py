import datetime
import re

import click

import app.input
import app.filter


def analyse(sprint, issue):

    start = datetime.datetime.strptime(
        sprint['startDate'], '%d/%b/%y %I:%M %p')
    end = datetime.datetime.strptime(
        sprint['endDate'], '%d/%b/%y %I:%M %p')
    tracks = re.compile('\[([0-9]+)h([0-9]+)m\]')
    minutes = 0

    for comment in issue.fields.comment.comments:
        created = datetime.datetime.strptime(
            re.sub(r'\..*$', '', comment.created), '%Y-%m-%dT%H:%M:%S'
            )

        if not (start <= created <= end):
            continue

        for track in tracks.findall(comment.body):
            minutes += int(track[0]) * 60
            minutes += int(track[1])

    return minutes


def format(minutes):

    hours = 0

    if 0 < minutes:
        hours = int(minutes / 60)
        minutes %= 60

    return (hours, minutes)


@click.command()
@click.pass_obj
def dailybusiness(obj):

    session = obj
    jira = session.jira

    try:
        board, sprints = app.input.for_board(jira)
        id = app.input.for_sprint(jira, board, sprints)

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

    labels = app.input.for_labels()
    issues, report = app.filter.for_labels(jira, report, labels)

    minutes = 0
    progress = click.progressbar(
        report.all,
        bar_template='%(label)s [%(bar)s] %(info)s',
        label='Analysing time tracks:',
        show_eta=False
        )
    with progress as all:
        for key in all:
            minutes += analyse(sprint, issues[key])

    dailybusiness = format(minutes)

    click.echo('Found {0}h {1}m of daily business.'.format(*dailybusiness))

    click.echo('Done!')
