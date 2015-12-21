import collections
import datetime
import re

import click
import pygal

import app.filter
import app.input


class Burndown():

    def __init__(self, sprint, commitment, report, issues, customfield):

        self.sprint = sprint
        self.commitment = commitment
        self.report = report
        self.issues = issues
        self.timeline = collections.OrderedDict()
        self.customfield = customfield
        self.faulty = {}

        self.start = datetime.datetime.strptime(
            sprint['startDate'], '%d/%b/%y %I:%M %p'
            )
        self.end = datetime.datetime.strptime(
            sprint['endDate'], '%d/%b/%y %I:%M %p'
            )

        start = self.start.replace(hour=0, minute=0, second=0, microsecond=0)
        day = datetime.timedelta(days=1)

        while start <= self.end:
            self.timeline[start.strftime('%Y-%m-%d')] = {
                'date': start,
                'ideal': commitment,
                'completed': 0,
                'unplanned': 0
            }
            start += day

        self.calculate()

    def _calculate_completed(self):

        changes = {}
        completed = self.commitment

        # closed issues
        for key in self.report.completed:

            if 'Story' != self.issues[key].fields.issuetype.name:
                continue

            resolution = self._get_resolution_date(
                self.issues[key].changelog.histories
                )
            if not self.start <= resolution <= self.end:
                continue

            estimation = getattr(self.issues[key].fields, self.customfield)
            if estimation is None:
                self.faulty[key] = 'Estimation missing'

            change = resolution.strftime('%Y-%m-%d')
            if change not in changes:
                changes[change] = 0
            changes[change] += int(estimation or 0)

        # decreased story points
        for key in self.report.all:

            if 'Story' != self.issues[key].fields.issuetype.name:
                continue

            status = self.issues[key].fields.status.name

            for history in self.issues[key].changelog.histories:
                for item in history.items:

                    created = datetime.datetime.strptime(
                        re.sub(r'\..*$', '', history.created),
                        '%Y-%m-%dT%H:%M:%S'
                        )
                    if not (self.start <= created <= self.end):
                        continue

                    if 'status' == item.field:
                        status = item.toString

                    if 'Open' == status:
                        continue

                    if ('Story Points' == item.field and
                            item.fromString is not None):
                        estimationFrom = int(item.fromString or 0)
                        estimationTo = int(item.toString or 0)
                        diff = estimationTo - estimationFrom

                        if diff > 0:
                            continue

                        change = created.strftime('%Y-%m-%d')
                        if change not in changes:
                            changes[change] = 0
                        changes[change] += abs(diff)

        for date, entry in self.timeline.items():
            if date in changes:
                completed -= changes[date]
            entry['completed'] = completed

    def _calculate_ideal(self):

        items = self.timeline.items()
        ideal = self.commitment
        step = ideal / (len(items) - 1)

        for date, entry in self.timeline.items():
            entry['ideal'] = ideal
            ideal -= step
        entry['ideal'] = 0

    def _calculate_unplanned(self):

        changes = {}
        unplanned = self.commitment

        # added
        for key in self.report.added:

            if 'Story' != self.issues[key].fields.issuetype.name:
                continue

            for date in self._get_added_dates(
                    self.issues[key].changelog.histories):

                estimation = self._get_estimation_from_date(
                    date, self.issues[key].changelog.histories
                    )
                if estimation is None:
                    estimation = getattr(
                        self.issues[key].fields, self.customfield
                        )
                if estimation is None:
                    self.faulty[key] = 'Estimation missing'

                change = date.strftime('%Y-%m-%d')
                if change not in changes:
                    changes[change] = 0
                changes[change] += int(estimation or 0)

        # punted
        for key in self.report.punted:

            if 'Story' != self.issues[key].fields.issuetype.name:
                continue

            for date in self._get_punted_dates(
                    self.issues[key].changelog.histories):

                resolution = self._get_resolution_date(
                    self.issues[key].changelog.histories
                    )
                if resolution and not self.start <= resolution <= self.end:
                    continue

                estimation = self._get_estimation_from_date(
                    date, self.issues[key].changelog.histories
                    )
                if estimation is None:
                    estimation = getattr(
                        self.issues[key].fields, self.customfield
                        )
                if estimation is None:
                    self.faulty[key] = 'Estimation missing'

                change = date.strftime('%Y-%m-%d')
                if change not in changes:
                    changes[change] = 0
                changes[change] -= int(estimation or 0)

        # decreased/increased story points
        for key in self.report.all:

            if 'Story' != self.issues[key].fields.issuetype.name:
                continue

            status = self.issues[key].fields.status.name

            for history in self.issues[key].changelog.histories:
                for item in history.items:

                    created = datetime.datetime.strptime(
                        re.sub(r'\..*$', '', history.created),
                        '%Y-%m-%dT%H:%M:%S'
                        )
                    if not (self.start <= created <= self.end):
                        continue

                    if 'status' == item.field:
                        status = item.toString

                    if ('Story Points' == item.field and
                            item.fromString is not None):
                        estimationFrom = int(item.fromString or 0)
                        estimationTo = int(item.toString or 0)
                        diff = estimationTo - estimationFrom

                        if 'Open' != status and diff < 0:
                            continue

                        change = created.strftime('%Y-%m-%d')
                        if change not in changes:
                            changes[change] = 0
                        changes[change] += diff

        for date, entry in self.timeline.items():
            if date in changes:
                unplanned += changes[date]
            entry['unplanned'] = unplanned

    def _get_added_dates(self, histories):

        dates = []

        for history in histories:
            for item in history.items:

                created = datetime.datetime.strptime(
                    re.sub(r'\..*$', '', history.created), '%Y-%m-%dT%H:%M:%S'
                    )
                if not (self.start <= created <= self.end):
                    continue

                if ('Sprint' == item.field and
                        str(self.sprint['id']) in
                        str(item.to).replace(' ', '').split(',')):
                    dates.append(created)

        return dates

    def _get_estimation_from_date(self, date, histories):

        before = None
        after = None

        for history in histories:
            for item in history.items:

                created = datetime.datetime.strptime(
                    re.sub(r'\..*$', '', history.created), '%Y-%m-%dT%H:%M:%S'
                    )

                if 'Story Points' == item.field and item.toString:

                    if created <= date:
                        before = int(item.toString)
                    if created > date:
                        after = int(item.toString)

                if after:
                    return after

        return before

    def _get_punted_dates(self, histories):

        dates = []

        for history in histories:
            for item in history.items:

                created = datetime.datetime.strptime(
                    re.sub(r'\..*$', '', history.created), '%Y-%m-%dT%H:%M:%S'
                    )
                if not (self.start <= created <= self.end):
                    continue

                if 'Sprint' != item.field and str(self.sprint['id']):
                    continue

                current_sprint = str(self.sprint['id'])
                from_sprint = str(getattr(item, 'from'))
                to_sprint = str(getattr(item, 'to'))

                if from_sprint and current_sprint not in from_sprint:
                    continue

                if current_sprint not in to_sprint:
                    dates.append(created)

        return dates

    def _get_resolution_date(self, histories):

        for history in reversed(histories):
            for item in history.items:

                if 'resolution' == item.field and 'Done' == item.toString:
                    return datetime.datetime.strptime(
                        re.sub(r'\..*$', '', history.created),
                        '%Y-%m-%dT%H:%M:%S'
                        )

    def calculate(self):

        self._calculate_ideal()
        self._calculate_completed()
        self._calculate_unplanned()

    def get_timeline(self):

        dates = []
        ideal = []
        completed = []
        unplanned = []

        now = datetime.datetime.now()

        for date, entry in self.timeline.items():
            dates.append(entry['date'].strftime('%Y-%m-%d'))
            ideal.append(entry['ideal'])
            if entry['date'] <= now:
                completed.append(entry['completed'])
                unplanned.append(entry['unplanned'])

        return {
            'dates': dates,
            'ideal': ideal,
            'completed': completed,
            'unplanned': unplanned
        }


@click.command()
@click.argument('output', type=click.File('wb'))
@click.pass_obj
def burndown(obj, output=None):

    session = obj
    jira, customfield = (session.jira, session.customfield)

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

    commitment = click.prompt('Enter commitment', type=click.INT)
    burndown = Burndown(
        sprint, commitment, report, issues, customfield
        )
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
        interpolate='hermite',
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
