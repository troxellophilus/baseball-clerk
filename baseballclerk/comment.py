import random
import time
from typing import List, Union

import praw


_BYLINE = "^^^[Bug?](https://github.com/troxellophilus/baseball-clerk/issues)"


def _build_obj(comment: praw.models.Comment):
    time.sleep(2)
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
        pitcher = play['matchup']['pitcher']['fullName']
        batter = play['matchup']['batter']['fullName']

        event = play['playEvents'][-1]
        k = 'K' if event['details']['code'].lower() == 's' else 'ꓘ'
        pitch_type = event['details']['type']['description']
        count_b = event['count']['balls']
        speed = event['pitchData']['startSpeed']
        nasty = event['pitchData'].get('nastyFactor')
        if nasty:
            nasty_str = f"Nasty Factor: **{nasty}**."
        else:
            nasty_str = ''
    except (KeyError, AttributeError) as err:
        raise DataObjectError(err)

    body = f"# {k}\n\n**{pitcher}** strikes out **{batter}** on a **{count_b}-2** count with a **{speed} mph** {pitch_type}. {nasty_str}\n\n{_BYLINE}"
    comment = gamechat.reply(body)

    return _build_obj(comment)


DONGER_VERBS = [
    'cracks',
    'smashes',
    'crushes',
    'rips',
    'hammers',
    'socks',
    'nails'
]


def homerun(gamechat: praw.models.Submission, play: dict) -> dict:
    try:
        pitcher = play['matchup']['pitcher']['fullName']
        batter = play['matchup']['batter']['fullName']
        runs = play['result']['rbi']

        event = play['playEvents'][-1]
        pitch_type = event['details']['type']['description']
        pitch_speed = event['pitchData']['startSpeed']
        speed = event['hitData']['launchSpeed']
        angle = event['hitData']['launchAngle']
        distance = event['hitData']['totalDistance']
    except (IndexError, AttributeError) as err:
        raise DataObjectError(err)

    body = f"# HR\n\n**{batter}** {random.choice(DONGER_VERBS)} a **{pitch_speed} mph {pitch_type}** from **{pitcher}** for a **{runs}-run** home run.\n\nLaunch Speed: **{speed} mph**. Launch Angle: **{angle}°**. Distance: **{distance} ft**.\n\n{_BYLINE}"
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
    except KeyError as err:
        raise DataObjectError(err)

    batters_up_str = '\n\n'.join(batters_up)
    body = f"**Due Up ({half[:3]} {inning})**\n\n{batters_up_str}\n\n{_BYLINE}"
    comment = gamechat.reply(body)

    return _build_obj(comment)


def robbed(gamechat: praw.models.Submission, evo: dict):
    try:
        desc = evo['des']
        speed = evo['hit_speed']
        angle = evo['hit_angle']
        distance = evo['hit_distance']
        xba = evo['xba']
    except KeyError as err:
        raise DataObjectError(err)

    body = f"**Robbed**\n\n{desc}\n\nLaunch Speed: **{speed} mph**. Launch Angle: **{angle}°**. Distance: **{distance} ft**. Hit Probability: ***{xba}%***."
    comment = gamechat.reply(body)

    return _build_obj(comment)


def boxscore_linedrive(gamechat: praw.models.Submission, evo: dict):
    try:
        desc = evo['des']
        speed = evo['hit_speed']
        angle = evo['hit_angle']
        distance = evo['hit_distance']
        xba = evo['xba']
    except KeyError as err:
        raise DataObjectError(err)

    body = f"**Looks like a line drive in the box score...**\n\n{desc}\n\nLaunch Speed: **{speed} mph**. Launch Angle: **{angle}°**. Distance: **{distance} ft**. Hit Probability: ***{xba}%***."
    comment = gamechat.reply(body)

    return _build_obj(comment)


def default_mention_reply(message: praw.models.Comment, choices: List[str]) -> dict:
    body = f"{random.choice(choices)}"
    comment = message.reply(body)
    return _build_obj(comment)
