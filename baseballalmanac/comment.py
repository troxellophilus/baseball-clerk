from typing import Union

import praw


def _build_obj(comment: praw.models.Comment):
    return {
        'subreddit': comment.subreddit.display_name,
        'comment_id': comment.id,
        'parent_id': comment.parent_id,
        'body': comment.body
    }


def strikeout(gamechat: praw.models.Submission, play: dict):
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

    return _build_obj(comment)


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
