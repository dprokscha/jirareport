import click


def for_labels(jira, report, labels):

    issues = {}
    ignored = []

    progress = click.progressbar(
        report.all,
        bar_template='%(label)s [%(bar)s] %(info)s',
        label='Fetching issues:',
        show_eta=False
        )

    with progress as all:

        for key in all:
            issue = jira.issue(key, expand='changelog')
            il = issue.fields.labels

            if labels and not [label for label in labels if label in il]:
                ignored.append(key)
                continue

            issues[key] = issue

    status = [
        'completed',
        'incompleted',
        'added',
        'punted',
        'all'
    ]

    for key in ignored:
        for collection in status:
            if key in getattr(report, collection):
                getattr(report, collection).remove(key)

    return (issues, report)
