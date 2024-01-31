import datetime as dt
import helpers as hf
import pandas as pd
import time


def process_game(game,teams,main_config,test,pref,ify_user):
    game_parsed = hf.parse_cbb_game(game,teams)

    config = hf.combine_configs(main_config,game_parsed)
    design,text = hf.build_cbb(config,test=test)
    design.show()

    if design != 'prompt failed':
        if design is not None:
            title,description,tags=hf.generate_t_d_t_cbb(game_parsed)
            if pref == 'pre':
                title = title + ' pre-game'
            main_config['image'] = design
            main_config['title'] = title.title()
            main_config['description'] =  description
            main_config['tags'] =  tags
            main_config['design'] = design
            main_config['text'] = text
            ify_user.post(publish=True)
        return title

def daily_run(test = False, fake_date=None, limit = None, do_yesterday=True):
    design_config,shop_config = hf.get_config('cbb')
    main_config = hf.combine_configs(design_config,shop_config)
    ify_user = hf.shopify_printify(main_config,'cbb')
    cfbd_loader = hf.cfbp_handler(main_config['cfbd_api'],fake_date=fake_date)
    if fake_date is not None:
        date = fake_date
    else:
        date = dt.dt.today()
    teams = cfbd_loader.get_team_info()

    todays_games = hf.get_day_bball_games(date)
    yesterdays_games = hf.get_day_bball_games(date-dt.timedelta(days=1))

    print(f'{len(todays_games)} Games Today')
    print(f'{len(yesterdays_games)} Games Yesterday')
    if limit is not None:
        print(f'Limiting to {limit} games')
        todays_games = todays_games[:limit]
        yesterdays_games = yesterdays_games[:limit]
    if len(todays_games)>0:
        for i in range(len(todays_games)):
            try:
                game=todays_games.iloc[i]
                title = process_game(game,teams,main_config,test,pref='post',ify_user = ify_user)
                print(f'Created {title}')
            except Exception as e:
                print(f'Failed {title}')
                print(e)
    if do_yesterday:
        if len(yesterdays_games)>0:
            for i in range(len(yesterdays_games)):
                try:
                    game=yesterdays_games.iloc[i]
                    title = process_game(game,teams,main_config,test,pref='post',ify_user = ify_user)
                    print(f'Created {title}')
                except Exception as e:
                    print(f'Failed {title}')
                    print(e)
    print('5 m pause before store organizing')
    time.sleep(60*5)
    ify_user.cover_image_wrapper()

    # organize store
    team_names = list(teams.name)
    # delete all my collections and rebuild them with all products
    ify_user.reset_collections(team_names)



if __name__ == "__main__":
    daily_run(test=False,fake_date=pd.to_datetime('03-19-2023'),do_yesterday=False)
