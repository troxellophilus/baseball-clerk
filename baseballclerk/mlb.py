"""MLB statsapi requests."""

from typing import List, Optional

from baseballclerk import util


def _get_path(path: str) -> dict:
    """Cached request a statsapi url."""
    url = f"https://statsapi.mlb.com{path}"
    return util.cached_request_json(url)


def _get_gumbo(game_pk: str) -> dict:
    """Return a 'gumbo' live game feed."""
    path = f"/api/v1.1/game/{game_pk}/feed/live"
    return _get_path(path)


def completed_plays(game_pk: str) -> List[dict]:
    """List the gumbo completed plays for a game.

    Args:
        game_pk (str)

    Returns:
        List[dict]: The completed plays for the game.
    """
    gumbo = _get_gumbo(game_pk)
    plays = gumbo.get("liveData", {}).get("plays", {}).get("allPlays", [])
    return [p for p in plays if p["about"]["isComplete"]]


def due_up(game_pk: str) -> Optional[dict]:
    """Get live inning and due up batter data from gumbo.

    Args:
        game_pk (str)

    Returns:
        dict: Live inning and due up batter data.
    """
    gumbo = _get_gumbo(game_pk)

    game_state = gumbo["gameData"]["status"]["statusCode"].lower()
    if game_state in ("f", "s", "di", "d"):
        return None

    linescore = gumbo["liveData"]["linescore"]
    inning = linescore["currentInning"]
    inning_half = linescore["inningHalf"]
    inning_state = linescore.get("inningState").lower()

    if inning_state == "end":
        inning += 1
        inning_half = "Top"
    elif inning_state == "middle":
        inning_half = "Bottom"

    # Check if the game is over by rule, even if the state doesn't show yet
    if (
        inning >= 9
        and inning_half == "Bottom"
        and linescore["teams"]["home"]["runs"] > linescore["teams"]["away"]["runs"]
    ):
        # Going into the bottom of the inning and the home team is leading, so the game is over (home team won)
        return None
    elif (
        inning >= 10
        and inning_half == "Top"
        and linescore["teams"]["home"]["runs"] != linescore["teams"]["away"]["runs"]
    ):
        # Going into the top of the inning and we are not tied, so the game is over
        return None

    due_up = {"inning": inning, "inningHalf": inning_half}

    batter_profiles = [
        _get_path(linescore["offense"]["batter"]["link"])["people"][0],
        _get_path(linescore["offense"]["onDeck"]["link"])["people"][0],
        _get_path(linescore["offense"]["inHole"]["link"])["people"][0],
    ]

    batters = []
    for profile in batter_profiles:
        batters.append(
            {
                "fullName": profile["fullName"],
                "primaryNumber": profile["primaryNumber"],
                "batSide": profile["batSide"]["code"],
            }
        )

    due_up["batters"] = batters

    return due_up
