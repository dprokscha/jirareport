import click


def for_labels(jira, report, labels):

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
        for collection in ['completed', 'incompleted', 'added', 'punted', 'all']:
            if key in getattr(report, collection):
                getattr(report, collection).remove(key)

    return (issues, report)