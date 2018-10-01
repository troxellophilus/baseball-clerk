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
    parser.add_argument('subreddit')
    return parser.parse_args()


def main():
    args = _parse_args()
    praw_bot = args.praw_bot
    subreddit_name = args.subreddit

    datastore.init()

    reddit = praw.Reddit(praw_bot)
    subreddit = reddit.subreddit(subreddit_name)

    game_thread = baseballbot.active_game_thread(reddit, subreddit)
    game_pk = game_thread['game_pk']
    gamechat = reddit.submission(game_thread['post_id'])

    # Post gamechat linescore updates (due up batters, pitching changes, substitutions, etc.)
    due_up = mlb.due_up(game_pk)
    comment.due_up(gamechat, due_up)

    # Post gamechat announcements (statcast & other play by play data)
    for play in mlb.new_plays(game_pk):
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
