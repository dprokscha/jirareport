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
                print('sdf')
                getattr(report, collection).remove(key)

    return (issues, report)



"""
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
"""