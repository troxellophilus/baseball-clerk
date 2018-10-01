import argparse
import os
from typing import Tuple

import praw
import requests

from baseballalmanac import comment
from baseballalmanac import mlb


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--praw-bot', default='baseballalmanac', help="Name of oauth config in praw.ini file.")
    parser.add_argument('--data-dir')
    parser.add_argument('subreddit')
    return parser.parse_args()


class _Error(Exception):
    pass


class NoActiveGameError(_Error):
    pass


def active_game(reddit: praw.Reddit, subreddit: praw.models.Subreddit) -> Tuple[praw.models.Submission, str]:
    response = requests.get("http://baseballbot.io/game_threads.json")
    for game in response.json()['data']:
        if game.get('subreddit', {}).get('name', '').lower() == subreddit.display_name:
            gamechat = reddit.submission(game['post_id'])
            game_pk = game['game_pk']
            break
    else:
        raise NoActiveGameError()
    # TODO: Check stickies if it's not run by baseballbot
    return gamechat, game_pk


def main():
    args = _parse_args()
    praw_bot = args.praw_bot
    subreddit_name = args.subreddit

    # Create the directory for game data if necessary
    data_dir = os.path.join(os.getcwd(), '_baseballalmanac')
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    reddit = praw.Reddit(praw_bot)
    subreddit = reddit.subreddit(subreddit_name)

    gamechat, game_pk = active_game(reddit, subreddit)

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
