import collections
import json

from jira.client import JIRA as JIRAHandler


class JIRA(JIRAHandler):

    def sprint_report(self, board_id, sprint_id):
        r_json = self._get_json('rapid/charts/sprintreport?rapidViewId=%s&sprintId=%s' % (board_id, sprint_id),
                                base=self.AGILE_BASE_URL)

        issues = collections.namedtuple('Issues', 'completed incompleted added punted all')

        completed = []
        incompleted = []
        added = []
        punted = []
        all = []

        for issue in r_json['contents']['completedIssues']:
            completed.append(issue['key'])
            if issue['key'] not in all:
                all.append(issue['key'])

        for issue in r_json['contents']['incompletedIssues']:
            incompleted.append(issue['key'])
            if issue['key'] not in all:
                all.append(issue['key'])

        for key in r_json['contents']['issueKeysAddedDuringSprint'].keys():
            added.append(key)
            if key not in all:
                all.append(key)

        for issue in r_json['contents']['puntedIssues']:
            punted.append(issue['key'])
            if issue['key'] not in all:
                all.append(issue['key'])

        return issues(completed=completed,
                      incompleted=incompleted,
                      added=added,
                      punted=punted,
                      all=all)

    def reportable_sprints(self, board_id, ignored_sprint_ids=()):

        sprints = []

        for sprint in self.sprints(board_id):
            if sprint.state not in ("ACTIVE", "CLOSED"):
                continue

            if not ignored_sprint_ids or sprint.id not in ignored_sprint_ids:
                sprints.append(sprint)

        return sprints


def connect(server, username, password):
    try:
        jira = JIRA(basic_auth=(username, password),
                    options={'server': server})

    except Exception:
        return None

    return jira