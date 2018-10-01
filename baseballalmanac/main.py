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


def main():
    args = _parse_args()
    praw_bot = args.praw_bot
    exclude = args.exclude
    subreddits = args.subreddits_type

    if subreddits and exclude:
        subreddits = list(set(subreddits) - set(exclude))

    datastore.init()

    reddit = praw.Reddit(praw_bot)

    for game_thread in baseballbot.active_game_threads(reddit, subreddits):
        subreddit_name = game_thread['subreddit']['name']
        game_pk = game_thread['game_pk']
        gamechat = reddit.submission(game_thread['post_id'])

        # Post gamechat linescore updates (due up batters, pitching changes, substitutions, etc.)
        due_up = mlb.due_up(game_pk, subreddit_name)
        comment.due_up(gamechat, due_up)

        # Post gamechat announcements (statcast & other play by play data)
        for play in mlb.new_plays(game_pk, subreddit_name):
            event = play.get('result', {}).get('event', '').lower()
            if not event:
                continue
            if event == 'strikeout':
                comment.strikeout(gamechat, play)
            elif event == 'homerun':
                comment.homerun(gamechat, play)

        # Run message responses (stats, text faces)
        for item in reddit.inbox.unread():
            if isinstance(item, praw.models.Comment):
                comment.text_face(item)


if __name__ == '__main__':
    main()
