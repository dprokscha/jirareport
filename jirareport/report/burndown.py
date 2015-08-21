import collections
import datetime
import re


class Burndown():

    def __init__(self, sprint, commitment, report, issues):

        self.sprint = sprint
        self.commitment = commitment
        self.report = report
        self.issues = issues
        self.timeline = collections.OrderedDict()

        self.start = datetime.datetime.strptime(sprint['startDate'], '%d/%b/%y %I:%M %p')
        self.end = datetime.datetime.strptime(sprint['endDate'], '%d/%b/%y %I:%M %p')

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

        for key in self.report.completed:

            if 'Story' != self.issues[key].fields.issuetype.name:
                continue

            date = self._get_resolution_date(self.issues[key].changelog.histories)
            if not date:
                continue

            if date not in changes:
                changes[date] = 0
            changes[date] += int(self.issues[key].fields.customfield_10002)

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

            for date in self._get_added_dates(self.issues[key].changelog.histories):

                estimation = self._get_estimation_from_date(date, self.issues[key].changelog.histories)
                if estimation is None:
                    estimation = int(self.issues[key].fields.customfield_10002)

                change = date.strftime('%Y-%m-%d')
                if change not in changes:
                    changes[change] = 0
                changes[change] += estimation

        # punted
        for key in self.report.punted:

            if 'Story' != self.issues[key].fields.issuetype.name:
                continue

            for date in self._get_punted_dates(self.issues[key].changelog.histories):

                estimation = self._get_estimation_from_date(date, self.issues[key].changelog.histories)
                if estimation is None:
                    estimation = int(self.issues[key].fields.customfield_10002)

                change = date.strftime('%Y-%m-%d')
                if change not in changes:
                    changes[change] = 0
                changes[change] -= estimation

        # changed
        for key in self.report.all:

            if 'Story' != self.issues[key].fields.issuetype.name:
                continue

            for history in self.issues[key].changelog.histories:
                for item in history.items:

                    created = datetime.datetime.strptime(re.sub(r'\..*$', '', history.created), '%Y-%m-%dT%H:%M:%S')
                    if not (self.start <= created <= self.end):
                        continue

                    if 'Story Points' == item.field and item.fromString is not None:

                        diff = int(item.toString) - int(item.fromString)
                        if diff > 0:
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

                created = datetime.datetime.strptime(re.sub(r'\..*$', '', history.created), '%Y-%m-%dT%H:%M:%S')
                if not (self.start <= created <= self.end):
                    continue

                if 'Sprint' == item.field and str(self.sprint['id']) == item.to:
                    dates.append(created)

        return dates

    def _get_estimation_from_date(self, date, histories):

        before = None
        after = None

        for history in histories:
            for item in history.items:

                created = datetime.datetime.strptime(re.sub(r'\..*$', '', history.created), '%Y-%m-%dT%H:%M:%S')

                if 'Story Points' == item.field:

                    if created <= date:
                        before = int(item.toString)
                    if created > date:
                        after = int(item.toString)

                if None != after:
                    return after

        return before

    def _get_punted_dates(self, histories):

        dates = []

        for history in histories:
            for item in history.items:

                created = datetime.datetime.strptime(re.sub(r'\..*$', '', history.created), '%Y-%m-%dT%H:%M:%S')
                if not (self.start <= created <= self.end):
                    continue

                if 'Sprint' == item.field and str(self.sprint['id']) not in item.to:
                    dates.append(created)

        return dates

    def _get_resolution_date(self, histories):

        for history in reversed(histories):
            for item in history.items:

                if 'resolution' == item.field and 'Done' == item.toString:
                    created = datetime.datetime.strptime(re.sub(r'\..*$', '', history.created), '%Y-%m-%dT%H:%M:%S')
                    if self.start <= created <= self.end:
                        return created.strftime('%Y-%m-%d')

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