import datetime
import re

def analyse(comments):

    tracks = re.compile('\[([0-9]+)h([0-9]+)m\]')
    hours = 0
    minutes = 0

    for comment in comments:
        for track in tracks.findall(comment.body):

            minutes += int(track[0]) * 60
            minutes += int(track[1])

    if 0 < minutes:
        hours = int(minutes / 60)
        minutes %= 60

    return {
        'hours': hours,
        'minutes': minutes
    }

def average(length, hours, minutes):

    minutes = int(((hours * 60) + minutes) / length)

    hours = int(minutes / 60)
    minutes %= 60

    return {
        'hours': hours,
        'minutes': minutes
    }