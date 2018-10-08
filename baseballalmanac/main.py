import argparse
import os
from typing import Tuple

import praw
import requests

from baseballalmanac import baseballbot
from baseballalmanac import comment
from baseballalmanac import datastore
from baseballalmanac import mlb


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--praw-bot', default='baseballalmanac', help="Name of oauth config in praw.ini file.")

    def subreddits_type(arg: str):
        if arg.lower() == 'all':
            return None
        else:
            return [s.trim() for s in arg.split(',')]

    parser.add_argument('-e', '--exclude', type=subreddits_type, help="Comma separated list of subreddits to exclude.")
    parser.add_argument('subreddits', type=subreddits_type, help="Comma separated list of subreddits to run against, or 'all'")
    return parser.parse_args()


def due_up(game_pk: str, gamechat: praw.models.Submission):
    """Post gamechat linescore updates (due up batters, pitching changes, substitutions, etc.)."""
    due_up = mlb.due_up(game_pk)
    key = f"dueup-{game_pk}-{gamechat.subreddit.display_name}-{due_up['inning']}-{due_up['inningHalf']}"
    datastore.write(datastore.TBL_EVENT, key, due_up)
    if due_up and not comment.exists(key):
        comment.due_up(gamechat, due_up)


def play_by_play(game_pk: str, gamechat: praw.models.Submission):
    """Post gamechat announcements (statcast & other play by play data)."""
    for play in mlb.plays(game_pk):
        # Update stored play.
        key = f"play-{game_pk}-{gamechat.subreddit.display_name}-{play['atBatIndex']}"
        event = datastore.write(datastore.TBL_EVENT, key, play)

        # Skip if we've already commented on this play.
        if comment.exists(key):
            continue

        # Comment for the play if necessary.
        play_result = event.data.get('result', {}).get('event', '').lower()
        if not play_result:
            continue
        if play_result == 'strikeout':
            comment.strikeout(gamechat, event)
        elif play_result == 'homerun':
            comment.homerun(gamechat, event)


def main():
    args = _parse_args()
    praw_bot = args.praw_bot
    exclude = args.exclude
    subreddits = args.subreddits

    if subreddits and exclude:
        subreddits = list(set(subreddits) - set(exclude))

    datastore.init()

    reddit = praw.Reddit(praw_bot)

    for game_thread in baseballbot.active_game_threads(reddit, subreddits):
        game_pk = game_thread['game_pk']
        gamechat = reddit.submission(game_thread['post_id'])

        due_up(game_pk, gamechat)
        play_by_play(game_pk, gamechat)

    # Run message responses (stats, text faces)
    for item in reddit.inbox.unread():
        if isinstance(item, praw.models.Comment):
            comment.text_face(item)


if __name__ == '__main__':
    main()
