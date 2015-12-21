import click


def for_board(jira):

    board = click.prompt('Enter board ID', type=click.INT)

    click.echo('Verifying board ID: ', nl=False)

    sprints = jira.reportable_sprints(board)

    if not sprints:
        raise Exception(
            'There are no active or closed sprints '
            'for the given board ID {0}'.format(board)
            )

    click.secho('OK', fg='green')

    return (board, sprints)


def for_labels():

    labels = []

    if click.confirm('Filter issues for labels?'):

        while True:
            try:
                labels.append(click.prompt(
                    'Enter label (interrupt to leave)',
                    type=click.STRING
                    )
                )
            except Exception:
                break

    return labels


def for_sprint(jira, board, sprints):

    list = []
    progress = click.progressbar(
        sprints,
        bar_template='%(label)s [%(bar)s] %(info)s',
        label='Fetching sprints:',
        show_eta=False
        )

    with progress as sprints:
        for sprint in sprints:
            list.append(jira.get_sprint(board, sprint.id))

    list.sort(key=lambda sprint: sprint['startDate'])

    for sprint in list:
        click.echo('ID {0}, Created: {1}, Name: {2}'.format(
            sprint['id'],
            sprint['startDate'].strftime('%Y-%m-%d'),
            sprint['name']
            )
        )

    while True:
        id = click.prompt('Enter sprint ID', type=click.INT)
        if any(sprint['id'] == id for sprint in list):
            return id
        click.echo('Invalid sprint ID {0}'.format(id))
