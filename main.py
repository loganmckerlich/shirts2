import helpers as hf
from datetime import datetime as dt

def main():
    '''this function runs weekly'''
    cfbd_key, image_key = hf.key_reader()
    base_config = hf.get_config()
    cfbd = hf.cfbp_handler(cfbd_key)

    # refresh game scores
    cfbd.get_schedule(dt.now().year)

    # generate shirts for all games with new shirts
    # generate shirts for all games 2 weeks out
    games = read_from_s3
    for game in games:
        if game.score == 'new': # if this is a new store
            create_shirt
            post_shirt
        elif week2out==True: # if this game is newly 2 weeks out
            create_shirt
            post_shirt
        else:
            print('old game or already generated pre shirt')

