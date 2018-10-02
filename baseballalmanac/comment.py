import praw


def strikeout(gamechat: praw.models.Submission, play: dict):
    pitcher = play['matchup']['pitcher']['fullName']
    batter = play['matchup']['batter']['fullName']
    event = play['playEvents'][-1]

    k = 'K' if event['details']['code'].lower() == 's' else 'ꓘ'
    pitch_type = event['details']['type']['description']
    count_b = event['count']['balls']
    count_s = event['count']['strikes']
    speed = event['pitchData']['startSpeed']

    comment = f"**{k}**  {pitcher} strikes out {batter} on a {count_b}-{count_s} count with a {speed} mph {pitch_type}."
    gamechat.reply(comment)


def homerun(gamechat: praw.models.Submission, play: dict):
    # pitcher = play['matchup']['pitcher']['fullName']
    # batter = play['matchup']['batter']['fullName']
    # event = play['playEvents'][-1]

    # comment = f"**HOMERUN**  {batter} {random.choice(verbs)} a "
    raise NotImplementedError()


def due_up(gamechat: praw.models.Submission, due_up: dict):
    raise NotImplementedError()


def text_face(message: praw.models.Comment):
    raise NotImplementedError()
