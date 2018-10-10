import argparse
import os
from typing import Tuple

import praw
import requests

from baseballclerk import baseballbot
from baseballclerk import comment
from baseballclerk import datastore
from baseballclerk import mlb


EVENTS = datastore.Table('event')
COMMENTS = datastore.Table('comment')


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--praw-bot', default='baseballclerk', help="Name of oauth config in praw.ini file.")

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
    EVENTS[key] = due_up
    if due_up and not COMMENTS.get(key):
        cmnt = comment.due_up(gamechat, due_up)
        COMMENTS[key] = cmnt


def play_by_play(game_pk: str, gamechat: praw.models.Submission):
    """Post gamechat announcements (statcast & other play by play data)."""
    for idx, play in enumerate(mlb.completed_plays(game_pk)):
        # Update stored play.
        key = f"play-{game_pk}-{gamechat.subreddit.display_name}-{idx}"
        EVENTS[key] = play

        # Skip if we've already commented on this play.
        if COMMENTS.get(key):
            continue

        # Comment for the play if necessary.
        play_result = play.get('result', {}).get('event', '').lower()
        if not play_result:
            continue
        if play_result == 'strikeout':
            cmnt = comment.strikeout(gamechat, play)
            COMMENTS[key] = cmnt
        elif play_result == 'homerun':
            cmnt = comment.homerun(gamechat, play)
            COMMENTS[key] = cmnt


def main():
    args = _parse_args()
    praw_bot = args.praw_bot
    exclude = args.exclude
    subreddits = args.subreddits

    if subreddits and exclude:
        subreddits = list(set(subreddits) - set(exclude))

    # Connect the datastore and create tables if not existing.
    datastore.connect('BaseballClerk')
    EVENTS.create_if_needed()
    COMMENTS.create_if_needed()

    reddit = praw.Reddit(praw_bot)

    for game_thread in baseballbot.active_game_threads(reddit, subreddits):
        game_pk = game_thread['game_pk']
        gamechat = reddit.submission(game_thread['post_id'])

        due_up(game_pk, gamechat)
        play_by_play(game_pk, gamechat)

    for item in reddit.inbox.unread():
        if isinstance(item, praw.models.Comment):
            comment.text_face(item)


if __name__ == '__main__':
    main()