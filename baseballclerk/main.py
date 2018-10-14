import argparse
from dataclasses import dataclass
import datetime
import json
import logging
import os
import time
from typing import List,Tuple

import praw

from baseballclerk import baseballbot
from baseballclerk import comment
from baseballclerk import datastore
from baseballclerk import mlb
from baseballclerk import savant


EVENTS = datastore.Table('event')
COMMENTS = datastore.Table('comment')


@dataclass
class _Config(object):

    subreddits: List[dict]

    @classmethod
    def from_path(cls, filepath: str):
        with open(filepath) as conf_fo:
            conf = json.load(conf_fo)
        return cls(**conf)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=_Config.from_path, help="Path to a local configuration JSON file.")
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

    bots_and_game_threads = []
    for game_thread in baseballbot.active_game_threads():
        subreddit_name = game_thread['subreddit']['name']
        if subreddit_name in config.subreddits:
            praw_bot = config.subreddits[subreddit_name]['praw_bot']
            bots_and_game_threads.append((praw_bot, game_thread))

    for praw_bot, game_thread in bots_and_game_threads:
        reddit = praw.Reddit(praw_bot)

        game_pk = game_thread['game_pk']
        gamechat = reddit.submission(game_thread['post_id'])

        play_by_play(game_pk, gamechat)
        due_up(game_pk, gamechat)

        time.sleep(2)

    for praw_bot in set(b for b, _ in bots_and_game_threads):
        reddit = praw.Reddit(praw_bot)

        for item in reddit.inbox.unread():
            if isinstance(item, praw.models.Comment) and 'baseballclerk' in item.body.lower():
                key = f"textface-{item.id}"
                cmnt = comment.text_face(item)
                item.mark_read()
                COMMENTS[key] = cmnt


if __name__ == '__main__':
    main()
