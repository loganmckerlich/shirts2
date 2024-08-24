import yaml
import pandas as pd
import math
import json
import requests
from PIL import Image
from unidecode import unidecode
import os
import logging

logger = logging.getLogger()


def new_football_season():
    # this checks if its a new season
    # if it is I need to rerun the teams query
    return True


def key_reader(version):
    logger.info(f'private file size: {os.path.getsize("info/private.yml")}')
    with open("info/private.yml", "r") as f:
        private_yml = yaml.safe_load(f)
    cfbd_api_key = private_yml["cfbd_api_key"]
    dalle_key = private_yml["dalle_key"]
    printify_access = private_yml[version]["printify_access"]
    shopify_access = private_yml[version]["shopify_access"]
    insta_pw = private_yml[version]["instagram"]["password"]
    insta_un = private_yml[version]["instagram"]["username"]
    email_pw = private_yml[version]["instagram"]["epassword"]
    email_un = private_yml[version]["instagram"]["eusername"]

    return (
        cfbd_api_key,
        dalle_key,
        printify_access,
        shopify_access,
        insta_pw,
        insta_un,
        email_pw,
        email_un,
    )


def get_config(version):
    with open("info/design_config.yml", "r") as f:
        design_config = yaml.safe_load(f)
    with open("info/shop_config.yml", "r") as f:
        shop_config = yaml.safe_load(f)
    (
        cfbd_api_key,
        dalle_key,
        printify_access,
        shopify_access,
        insta_pw,
        insta_un,
        email_pw,
        email_un,
    ) = key_reader(version)
    design_config["cfbd_api"] = cfbd_api_key
    design_config["dalle_key"] = dalle_key
    shop_config["printify_access"] = printify_access
    shop_config["shopify_access"] = shopify_access
    shop_config["instagram"] = {}
    shop_config["instagram"]["username"] = insta_un
    shop_config["instagram"]["password"] = insta_pw
    shop_config["instagram"]["eusername"] = email_un
    shop_config["instagram"]["epassword"] = email_pw

    return design_config, shop_config


def parse_game(game, teams):
    """
    takes in a row from my games table as game

    and my teams table

    assembles all info needed to create the image

    """
    home = teams.loc[teams.id == game["home_id"]]
    away = teams.loc[teams.id == game["away_id"]]

    if (
        (game["complete"])
        and (not math.isnan(game["home_score"]))
        and (not math.isnan(game["away_score"]))
    ):
        gscore = (int(game["home_score"]), int(game["away_score"]))
    else:
        gscore = (None, None)

    game_config = {
        "home_team": {
            "shortn": home.name.values[0],
            "longn": f"University Of {home.name.values[0]} {home.mascot.values[0]}",
            "color": home.color.values[0],
            "logo": home.logos.values[0],
            "mascot": home.mascot.values[0],
            "rank":game["home_rank"]

        },
        "away_team": {
            "shortn": away.name.values[0],
            "longn": f"University Of {away.name.values[0]} {away.mascot.values[0]}",
            "color": away.color.values[0],
            "logo": away.logos.values[0],
            "mascot": away.mascot.values[0],
            "rank":game["away_rank"]
        },
        "sport": "football",
        "game": {
            "date": pd.to_datetime(game["startdate"]).strftime(format="%d %b, %Y"),
            "score": gscore,
            "done": game["complete"],
            "week": game["week"],
        },
    }
    return game_config


def parse_cbb_game(game, team_info):
    team_info["joiner"] = team_info.name.apply(lambda x: unidecode(x).lower())
    team1_joiner = unidecode(game.team1).lower()
    team1_info = team_info.loc[team_info.joiner == team1_joiner].to_dict("records")
    if len(team1_info) < 1:
        team1_info = team_info.loc[team_info.abrev == game.team1].to_dict("records")
    if len(team1_info) < 1:
        team1_info = [
            {"color": "#FFFFFF", "mascot": None, "logos": None, "long_name": game.team1}
        ]
    team2_joiner = unidecode(game.team2).lower()
    team2_info = team_info.loc[team_info.joiner == team2_joiner].to_dict("records")
    if len(team2_info) < 1:
        team2_info = team_info.loc[team_info.abrev == game.team2].to_dict("records")
    if len(team2_info) < 1:
        team2_info = [
            {"color": "#FFFFFF", "mascot": None, "logos": None, "long_name": game.team2}
        ]
    team1_info = team1_info[0]
    team2_info = team2_info[0]

    game_out = {
        "team1": {
            "name": game.team1.replace("(", "").replace(")", ""),
            "rank": game.team1Rank,
            "score": game.team1Score,
            "color": team1_info["color"],
            "mascot": team1_info["mascot"],
            "logo": team1_info["logos"],
            "long_name": team1_info["long_name"],
        },
        "team2": {
            "name": game.team2.replace("(", "").replace(")", ""),
            "rank": game.team2Rank,
            "score": game.team2Score,
            "color": team2_info["color"],
            "mascot": team2_info["mascot"],
            "logo": team2_info["logos"],
        },
        "date": pd.to_datetime(game.date_).strftime(format="%d %b, %Y"),
        "desc": game.Desc,
    }
    return game_out


def combine_configs(base_config, game_config):
    base_config.update(game_config)
    return base_config


def generate_t_d_t(game_config):
    title = f"{game_config['home_team']['shortn']} vs {game_config['away_team']['shortn']}. {game_config['game']['date']}. {game_config['game']['week']}"
    if game_config["game"]["done"]:
        before = ""
        mid = f"{game_config['game']['score'][0]} to {game_config['game']['score'][1]} "
        mid2 = "played at "
    else:
        before = "Created before the game has been played. "
        mid = ""
        mid2 = "to be played "

    description = (
        before
        + f"AI image representing the football game "
        + mid
        + f"between {game_config['home_team']['shortn']} and {game_config['away_team']['shortn']}, {mid2} {game_config['game']['date']}"
        + f"/n||{game_config['home_team']['shortn']}|| ||{game_config['away_team']['shortn']}||"
    )
    tags = f"football,college,sports,{game_config['home_team']['shortn']},{game_config['away_team']['shortn']}"

    return title, description, tags


def generate_t_d_t_cbb(game_config):
    title = f"{game_config['team1']['name']} vs {game_config['team2']['name']}. {game_config['date']}"
    if game_config["team1"]["score"] is not None:
        before = ""
        mid = f"{game_config['team1']['score']} to {game_config['team2']['score']} "
        mid2 = "played at "
    else:
        before = "Created before the game has been played, Score Not yet available. "
        mid = ""
        mid2 = "to be played "

    description = (
        "Unisex! Sizes are in mens.\n "
        + before
        + f"AI image representing the basketball game "
        + mid
        + f"between {game_config['team1']['name']} and {game_config['team2']['name']}, {mid2} {game_config['date']} "
        + "\n"
        + f"{game_config['team1']['name']} {game_config['team1']['mascot']} basketball shirt {game_config['team2']['name']} {game_config['team2']['mascot']} basketball shirt"
        + f"\n||{game_config['team1']['name']}|| ||{game_config['team2']['name']}||"
        + f"ROUND: ||{game_config['desc']}||"
    )
    tags = f"basketball,marchmadness,march,madness,college,sports,{game_config['team1']['name']},{game_config['team1']['name']}basketball,{game_config['team2']['name']}{game_config['team2']['name']}"

    return title, description, tags


def most_frequent(List):
    if len(set(List)) > 1:
        logger.info("There are multiple weeks represented in these games")
    return max(set(List), key=List.count)
