import yaml
import pandas as pd
import math
import json

def new_football_season():
    # this checks if its a new season
    # if it is I need to rerun the teams query
    pass

def key_reader():
    with open('private.yml','r') as f:
        private_yml = yaml.safe_load(f)
    cfbd_api_key = private_yml['cfbd_api_key']
    sd_api_key = private_yml['sd_api_key']
    printify_access = private_yml['printify_access']
    shopify_access = private_yml['shopify_access']

    return cfbd_api_key,sd_api_key,printify_access,shopify_access

def get_config():
    with open('design_config.yml','r') as f:
        base_config = yaml.safe_load(f)
    with open('shop_config.yml','r') as f:
        shop_config = yaml.safe_load(f)
    cfbd_api_key,sd_api_key,printify_access,shopify_access = key_reader()
    base_config['cfbd_api'] = cfbd_api_key
    base_config['sd_api'] = sd_api_key
    shop_config['printify_access'] = printify_access
    shop_config['shopify_access'] = shopify_access
    return base_config,shop_config

def parse_game(game,teams):
    '''
    takes in a row from my games table as game

    and my teams table

    assembles all info needed to create the image
    
    '''
    home = teams.loc[teams.id==game['home_id']]
    away = teams.loc[teams.id==game['away_id']]
    if (game['complete']) and (not math.isnan(game['home_score'])) and (not math.isnan(game['away_score'])):
        gscore = (int(game['home_score']),int(game['away_score']))
    else:
        gscore = (None,None)

    game_config = {
        'home_team':{
            'shortn':home.name.values[0],
            'longn':f'University Of {home.name.values[0]} {home.mascot.values[0]}',
            'color':home.color.values[0],
            'logo':home.logos.values[0]
        },
        'away_team':{
            'shortn':away.name.values[0],
            'longn':f'University Of {away.name.values[0]} {away.mascot.values[0]}',
            'color':away.color.values[0],
            'logo':away.logos.values[0]
        },
        'sport':'football',
        'game':{
            'date':pd.to_datetime(game['startdate']).strftime(format="%d %b, %Y"),
            'score':gscore,
            'done':game['complete']
        }
    }
    return game_config

def combine_configs(base_config,game_config):
    base_config.update(game_config)
    return base_config