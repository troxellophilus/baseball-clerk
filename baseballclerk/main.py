import argparse
from dataclasses import dataclass
import datetime
import json
import logging
import os
import time
from typing import Dict, List, Tuple

import praw

from baseballclerk import baseballbot
from baseballclerk import comment
from baseballclerk import datastore
from baseballclerk import mlb
from baseballclerk import savant


EVENTS = datastore.Table('event')
COMMENTS = datastore.Table('comment')


def _parse_args():
    parser = argparse.ArgumentParser()

    def config_from_path(filepath: str):
        with open(filepath) as conf_fo:
            config = json.load(conf_fo)
        return config

    parser.add_argument('config', type=config_from_path, help="Path to a local configuration JSON file.")
    return parser.parse_args()


def due_up(game_pk: str, gamechat: praw.models.Submission):
    """Post gamechat linescore updates (due up batters, pitching changes, substitutions, etc.)."""
    due_up = mlb.due_up(game_pk)
    key = f"dueup-{game_pk}-{gamechat.subreddit.display_name}-{due_up['inning']}-{due_up['inningHalf']}"
    if due_up and not COMMENTS.get(key):
        EVENTS[key] = due_up
        try:
            cmnt = comment.due_up(gamechat, due_up)
            COMMENTS[key] = cmnt
        except comment.DataObjectError as err:
            logging.error(err)


def play_by_play(game_pk: str, gamechat: praw.models.Submission):
    """Post gamechat announcements (statcast & other play by play data)."""
    for idx, play in enumerate(mlb.completed_plays(game_pk)):
        # Update stored play.
        key = f"play-{game_pk}-{gamechat.subreddit.display_name}-{idx}"
        EVENTS[key] = play

        # Skip if it isn't fresh.
        end_time = datetime.datetime.fromisoformat(play['playEndTime'].rstrip('Z'))
        if (datetime.datetime.utcnow() - end_time).seconds > 300:
            continue

        # Skip if we've already commented on this play.
        if COMMENTS.get(key):
            continue

        # Comment for the play if necessary.
        play_result = play.get('result', {}).get('event', '').lower()
        if not play_result:
            continue
        if play_result == 'strikeout':
            try:
                cmnt = comment.strikeout(gamechat, play)
                COMMENTS[key] = cmnt
            except comment.DataObjectError as err:
                logging.error(err)
        elif play_result == 'home run':
            try:
                cmnt = comment.homerun(gamechat, play)
                COMMENTS[key] = cmnt
            except comment.DataObjectError as err:
                logging.error(err)


def exit_velocities(game_pk: str, gamechat: praw.models.Submission):
    for idx, evo in enumerate(savant.exit_velocities(game_pk)):
        # Update stored evo.
        key = f"evo-{game_pk}-{gamechat.subreddit.display_name}-{idx}"
        EVENTS[key] = evo

        # Skip if we've already commented on this play.
        if COMMENTS.get(key):
            continue

        # Comment for the play if necessary.
        if not ('xba' in evo and 'is_bip_out' in evo and evo.get('des')):
            continue
        xba = int(evo['xba'])
        is_bip_out = evo['is_bip_out'].lower() == 'y'
        if xba > 80 and is_bip_out:
            try:
                cmnt = comment.robbed(gamechat, evo)
                COMMENTS[key] = cmnt
            except comment.DataObjectError as err:
                logging.error(err)
        elif xba < 10 and not is_bip_out:
            try:
                cmnt = comment.boxscore_linedrive(gamechat, evo)
                COMMENTS[key] = cmnt
            except comment.DataObjectError as err:
                logging.error(err)


def main():
    args = _parse_args()
    config = args.config

    # Connect the datastore and create tables if not existing.
    datastore.connect('BaseballClerk.db')
    EVENTS.create_if_needed()
    COMMENTS.create_if_needed()

    # Build list of (subreddit_config: dict, game_thread: dict) tuples.
    subreddit_configs_and_game_threads = []
    for game_thread in baseballbot.active_game_threads():
        subreddit_name = game_thread['subreddit']['name']
        if subreddit_name in config['subreddits']:
            subreddit_config = config['subreddits'][subreddit_name]
            subreddit_configs_and_game_threads.append((subreddit_config, game_thread))

    for game_thread in baseballbot.active_game_threads():
        subreddit_config = config['subreddits'].get(game_thread['subreddit']['name'])  # type: dict
        if not subreddit_config:
            continue

        reddit = praw.Reddit(subreddit_config['praw_bot'])

        game_pk = game_thread['game_pk']
        gamechat = reddit.submission(game_thread['post_id'])

        play_by_play(game_pk, gamechat)
        due_up(game_pk, gamechat)

        time.sleep(2)

    for subreddit_config in config['subreddits'].values():
        reddit = praw.Reddit(subreddit_config['praw_bot'])

        for item in reddit.inbox.unread():
            if isinstance(item, praw.models.Comment) and 'baseballclerk' in item.body.lower():
                key = f"textface-{item.id}"
                cmnt = comment.default_mention_reply(item, subreddit_config['default_replies'])
                item.mark_read()
                COMMENTS[key] = cmnt


if __name__ == '__main__':
    main()
