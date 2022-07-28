"""Reddit comment handler."""

import random
import time
from typing import List

import backoff
import praw
import praw.exceptions
from praw.models import Comment, Submission


_BYLINE = "^^^[⚾](https://github.com/troxellophilus/baseball-clerk/issues)"

_MAX_TRIES = 4


def _build_obj(comment: Comment):
    """Build a datastore-able dict for a comment."""
    time.sleep(2)
    return {
        "subreddit": comment.subreddit.display_name,
        "comment_id": comment.id,
        "parent_id": comment.parent_id,
        "body": comment.body,
    }


class _Err(Exception):
    pass


class DataObjectError(_Err):
    """Error thrown when comment function cannot process data objects."""

    pass


@backoff.on_exception(
    backoff.expo, praw.exceptions.APIException, max_tries=_MAX_TRIES, jitter=None
)
def strikeout(gamechat: Submission, play: dict) -> dict:
    """Post a comment to the game thread for a strikeout play.

    Args:
        gamechat (Submission): The destination game thread.
        play (dict): The strikeout play data.

    Returns:
        dict: The posted comment metadata as a datastore-able dict.
    """
    try:
        pitcher = play["matchup"]["pitcher"]["fullName"]
        batter = play["matchup"]["batter"]["fullName"]

        event = play["playEvents"][-1]
        k = "ꓘ" if event["details"]["code"].lower() == "c" else "K"
        pitch_type = event["details"]["type"]["description"]
        count_b = event["count"]["balls"]

        pitch_data = event["pitchData"]
        speed = pitch_data["startSpeed"]

        breaks = pitch_data.get("breaks", {})
        spin_rate = breaks.get("spinRate")
        break_length = breaks.get("breakLength")

        pitch_details = [e["details"] for e in play["playEvents"] if "pitchData" in e]
        sequence = ", ".join(
            f"{d['type']['code']} *({d['code'].strip('*').lower()})*"
            for d in pitch_details
        )
    except (KeyError, AttributeError) as err:
        raise DataObjectError(f"{err.__class__.__name__}: {err}")

    if spin_rate and break_length:
        break_details = (
            f"Spin Rate: **{spin_rate} rpm**. Break Length: **{break_length} in**.\n\n"
        )
    else:
        break_details = ""

    body = f"# {k}\n\n**{pitcher}** strikes out **{batter}** on a **{count_b}-2** count with a **{speed} mph** {pitch_type}.\n\n{break_details}*Sequence ({len(pitch_details)}):* {sequence}\n\n{_BYLINE}"
    comment = gamechat.reply(body)

    return _build_obj(comment)


# Constant set of verbs to choose from for home runs.
DONGER_VERBS = ["cracks", "smashes", "crushes", "rips", "hammers", "socks", "nails"]


@backoff.on_exception(
    backoff.expo, praw.exceptions.APIException, max_tries=_MAX_TRIES, jitter=None
)
def homerun(gamechat: Submission, play: dict) -> dict:
    """Post a comment to the game thread for a homerun play.

    Args:
        gamechat (Submission): The destination game thread.
        play (dict): The homerun play data.

    Returns:
        dict: The posted comment metadata as a datastore-able dict.
    """
    try:
        pitcher = play["matchup"]["pitcher"]["fullName"]
        batter = play["matchup"]["batter"]["fullName"]
        runs = play["result"]["rbi"]

        event = play["playEvents"][-1]
        pitch_type = event["details"]["type"]["description"]
        pitch_speed = event["pitchData"]["startSpeed"]
        speed = event["hitData"]["launchSpeed"]
        angle = event["hitData"]["launchAngle"]
        distance = event["hitData"]["totalDistance"]
    except (KeyError, AttributeError) as err:
        raise DataObjectError(f"{err.__class__.__name__}: {err}")

    body = f"# HR\n\n**{batter}** {random.choice(DONGER_VERBS)} a **{pitch_speed} mph {pitch_type}** from **{pitcher}** for a **{runs}-run** home run.\n\nLaunch Speed: **{speed} mph**. Launch Angle: **{angle}°**. Distance: **{distance} ft**.\n\n{_BYLINE}"
    comment = gamechat.reply(body)

    return _build_obj(comment)


@backoff.on_exception(
    backoff.expo, praw.exceptions.APIException, max_tries=_MAX_TRIES, jitter=None
)
def due_up(gamechat: Submission, due_up: dict) -> dict:
    """Post a comment to the game thread for the players due up.

    Args:
        gamechat (Submission): The destination game thread.
        due_up (dict): The due up players data.

    Returns:
        dict: The posted comment metadata as a datastore-able dict.
    """
    try:
        inning = due_up["inning"]
        half = due_up["inningHalf"]

        batters_up = []
        for batter in due_up["batters"]:
            hand = batter["batSide"]
            name = batter["fullName"]
            batters_up.append(f"{hand} {name}")
    except KeyError as err:
        raise DataObjectError(f"{err.__class__.__name__}: {err}")

    batters_up_str = "\n\n".join(batters_up)
    body = f"**Due Up ({half[:3]} {inning})**\n\n{batters_up_str}\n\n{_BYLINE}"
    comment = gamechat.reply(body)

    return _build_obj(comment)


@backoff.on_exception(
    backoff.expo, praw.exceptions.APIException, max_tries=_MAX_TRIES, jitter=None
)
def robbed(gamechat: Submission, evo: dict):
    """Post a comment to the game thread for a robbed hit.

    Args:
        gamechat (Submission): The destination game thread.
        evo (dict): The exit velocity data of the play.

    Returns:
        dict: The posted comment metadata as a datastore-able dict.
    """
    try:
        desc = evo["des"]
        speed = evo["hit_speed"]
        angle = evo["hit_angle"]
        distance = evo["hit_distance"]
        xba = evo["xba"]
    except KeyError as err:
        raise DataObjectError(f"{err.__class__.__name__}: {err}")

    body = f"**Robbed**\n\n{desc}\n\nLaunch Speed: **{speed} mph**. Launch Angle: **{angle}°**. Distance: **{distance} ft**. Expected Batting Average: ***{xba}***.\n\n{_BYLINE}"
    comment = gamechat.reply(body)

    return _build_obj(comment)


@backoff.on_exception(
    backoff.expo, praw.exceptions.APIException, max_tries=_MAX_TRIES, jitter=None
)
def boxscore_linedrive(gamechat: Submission, evo: dict):
    """Post a comment to the game thread for a low hp hit.

    Args:
        gamechat (Submission): The destination game thread.
        evo (dict): The exit velocity data of the play.

    Returns:
        dict: The posted comment metadata as a datastore-able dict.
    """
    try:
        desc = evo["des"]
        speed = evo["hit_speed"]
        angle = evo["hit_angle"]
        distance = evo["hit_distance"]
        xba = evo["xba"]
    except KeyError as err:
        raise DataObjectError(f"{err.__class__.__name__}: {err}")

    body = f"*Looks like a line drive in the box score...*\n\n{desc}\n\nLaunch Speed: **{speed} mph**. Launch Angle: **{angle}°**. Distance: **{distance} ft**. Expected Batting Average: ***{xba}***.\n\n{_BYLINE}"
    comment = gamechat.reply(body)

    return _build_obj(comment)


@backoff.on_exception(
    backoff.expo, praw.exceptions.APIException, max_tries=_MAX_TRIES, jitter=None
)
def default_mention_reply(message: Comment, choices: List[str]) -> dict:
    """Post a random selection of choices as a reply to a message.

    Args:
        message (Comment): The message to respond to.
        choices (List[str]): The reply body options to choose from.

    Returns:
        dict: The posted comment metadata as a datastore-able dict.
    """
    body = f"{random.choice(choices)}"
    comment = message.reply(body)
    return _build_obj(comment)
