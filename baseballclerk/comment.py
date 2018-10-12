import random
from typing import Union

import praw


def _build_obj(comment: praw.models.Comment):
    return {
        'subreddit': comment.subreddit.display_name,
        'comment_id': comment.id,
        'parent_id': comment.parent_id,
        'body': comment.body
    }


class _Err(Exception):
    pass


class DataObjectError(_Err):
    pass


def strikeout(gamechat: praw.models.Submission, play: dict) -> dict:
    try:
        pitcher = play.data['matchup']['pitcher']['fullName']
        batter = play.data['matchup']['batter']['fullName']

        event = play.data['playEvents'][-1]
        k = 'K' if event['details']['code'].lower() == 's' else 'ꓘ'
        pitch_type = event['details']['type']['description']
        count_b = event['count']['balls']
        speed = event['pitchData']['startSpeed']
    except (IndexError, AttributeError) as err:
        raise DataObjectError(err)

    body = f"**{k}**  {pitcher} strikes out {batter} on a {count_b}-2 count with a {speed} mph {pitch_type}."
    comment = gamechat.reply(body)

    return _build_obj(comment)


DONGER_VERBS = [
    'cracks',
    'smashes',
    'crushes',
    'rips',
    'hammers',
    'socks',
    'unleashes'
]


def homerun(gamechat: praw.models.Submission, play: dict) -> dict:
    try:
        pitcher = play['matchup']['pitcher']['fullName']
        batter = play['matchup']['batter']['fullName']
        runs = play['results']['rbi']

        event = play['playEvents'][-1]
        pitch_type = event['details']['type']['description']
        speed = event['hitData']['launchSpeed']
        angle = event['hitData']['launchAngle']
        distance = event['hitData']['totalDistance']
    except (IndexError, AttributeError) as err:
        raise DataObjectError(err)

    body = f"**HOME RUN**  {batter} {random.choice(DONGER_VERBS)} a {pitch_type} from {pitcher} {distance} ft for a {runs}-run home run.\n\nLaunch Speed: **{speed}** mph\n\nLaunch Angle: **{angle}**°"
    comment = gamechat.reply(body)

    return _build_obj(comment)


def due_up(gamechat: praw.models.Submission, due_up: dict) -> dict:
    try:
        inning = due_up['inning']
        half = due_up['inningHalf']

        batters_up = []
        for batter in due_up['batters']:
            hand = batter['batSide']
            name = batter['fullName']
            batters_up.append(f"{hand} {name}")
    except (IndexError, AttributeError) as err:
        raise DataObjectError(err)

    body = f"**Due Up ({half} {inning})**  {', '.join(batters_up)}"
    comment = gamechat.reply(body)

    return _build_obj(comment)


TEXT_FACES = [
    '(✿◠‿◠)',
    '(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧',
    '(◡‿◡✿)',
    '( ́ ◕◞ε◟◕`)',
    '(｡◕‿◕｡)',
    '(☞ﾟ∀ﾟ)☞'
]


def text_face(message: praw.models.Comment) -> dict:
    body = f"{random.choice(TEXT_FACES)}"
    comment = message.reply(body)
    return _build_obj(comment)
