import datetime
import re

def analyse(sprint, issue):

    start = datetime.datetime.strptime(sprint['startDate'], '%d/%b/%y %I:%M %p')
    end = datetime.datetime.strptime(sprint['endDate'], '%d/%b/%y %I:%M %p')
    tracks = re.compile('\[([0-9]+)h([0-9]+)m\]')
    minutes = 0

    for comment in issue.fields.comment.comments:
        created = datetime.datetime.strptime(re.sub(r'\..*$', '', comment.created), '%Y-%m-%dT%H:%M:%S')

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