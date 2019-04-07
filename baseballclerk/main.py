"""Baseball Clerk live baseball updates for Reddit game threads."""

import argparse
import datetime
import json
import logging
import time

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
        with open(filepath, encoding='utf-8') as conf_fo:
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
    """Post gamechat announcements for BaseballSavant data (i.e. hit probability data)."""
    for idx, evo in enumerate(savant.exit_velocities(game_pk)):
        # Update stored evo.
        key = f"evo-{game_pk}-{gamechat.subreddit.display_name}-{idx}"
        EVENTS[key] = evo

        # Skip if we've already commented on this play.
        if COMMENTS.get(key):
            continue

        # Comment for the play if necessary.
        if not ('xba' in evo and 'is_bip_out' in evo and evo.get('des', '').strip()):
            continue

        xba = float(evo['xba'])
        is_bip_out = evo['is_bip_out'].lower() == 'y'
        is_hit = evo.get('result', '').lower() in ('single', 'double', 'triple', 'home run')

        if xba > 0.90 and is_bip_out:
            try:
                cmnt = comment.robbed(gamechat, evo)
                COMMENTS[key] = cmnt
            except comment.DataObjectError as err:
                logging.error(err)
        elif xba < 0.10 and not is_bip_out and is_hit:
            try:
                cmnt = comment.boxscore_linedrive(gamechat, evo)
                COMMENTS[key] = cmnt
            except comment.DataObjectError as err:
                logging.error(err)


def main():
    """Write and post new BaseballClerk comments."""
    logging.basicConfig(format="%(levelname)s:%(module)s:%(filename)s:%(lineno)s:%(message)s")

    args = _parse_args()
    config = args.config

    # Connect the datastore and create tables if not existing.
    datastore.connect('BaseballClerk.db')
    EVENTS.create_if_needed()
    COMMENTS.create_if_needed()

    for game_thread in baseballbot.active_game_threads():
        subreddit_config = config['subreddits'].get(game_thread['subreddit']['name'])  # type: dict
        if not subreddit_config:
            continue

        reddit = praw.Reddit(subreddit_config['praw_bot'])

        game_pk = game_thread['gamePk']
        gamechat = reddit.submission(game_thread['postId'])

        play_by_play(game_pk, gamechat)
        exit_velocities(game_pk, gamechat)
        due_up(game_pk, gamechat)

        time.sleep(2)

    for subreddit_config in config['subreddits'].values():
        praw_bot = subreddit_config['praw_bot']
        reddit = praw.Reddit(praw_bot)

        for item in reddit.inbox.unread():
            # Make sure it is fresh.
            created_utc = datetime.datetime.fromtimestamp(item.created_utc)
            if (datetime.datetime.utcnow() - created_utc).seconds > 600:
                item.mark_read()
                continue

            if isinstance(item, praw.models.Comment) and praw_bot.lower() in item.body.lower():
                key = f"textface-{item.id}"
                cmnt = comment.default_mention_reply(item, subreddit_config['default_replies'])
                COMMENTS[key] = cmnt

            item.mark_read() # Keep the inbox clean.


if __name__ == '__main__':
    main()
