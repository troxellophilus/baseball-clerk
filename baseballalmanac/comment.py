from typing import Union

import praw

from baseballalmanac import datastore


def exists(key: str):
    return bool(datastore.read(datastore.TBL_COMMENT, key))


def _store(key: str, comment: praw.models.Comment):
    obj = {
        'subreddit': comment.subreddit.display_name,
        'comment_id': comment.id,
        'parent_id': comment.parent_id,
        'body': comment.body
    }
    datastore.write(datastore.TBL_COMMENT, key, obj)


def strikeout(gamechat: praw.models.Submission, play: datastore.StoredObject):
    pitcher = play.data['matchup']['pitcher']['fullName']
    batter = play.data['matchup']['batter']['fullName']
    event = play.data['playEvents'][-1]

    k = 'K' if event['details']['code'].lower() == 's' else 'ꓘ'
    pitch_type = event['details']['type']['description']
    count_b = event['count']['balls']
    count_s = event['count']['strikes']
    speed = event['pitchData']['startSpeed']

    body = f"**{k}**  {pitcher} strikes out {batter} on a {count_b}-{count_s} count with a {speed} mph {pitch_type}."
    comment = gamechat.reply(body)

    _store(play.key, comment)


def homerun(gamechat: praw.models.Submission, play: dict):
    # pitcher = play['matchup']['pitcher']['fullName']
    # batter = play['matchup']['batter']['fullName']
    # event = play['playEvents'][-1]

    # comment = f"**HOMERUN**  {batter} {random.choice(verbs)} a "
    raise NotImplementedError()


def due_up(gamechat: praw.models.Submission, due_up: dict):
    raise NotImplementedError()


def text_face(message: praw.models.Comment):
    raise NotImplementedError()
