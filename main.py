import helpers as hf
import datetime as dt
import time

def process_game(game,teams,design_config,s3_mover,game_id,test,shop_config,pref):
    print(f'    generating game image')
    game = game.to_dict('records')[0]
    game_config = hf.parse_game(game,teams)
    game_config['game_id'] = game
    config = hf.combine_configs(design_config,game_config)
    design,text = hf.build_design(config,test=False)

    # do I need to save all my images to s3?
    s3_mover.image_to_s3(design,rf"{pref}/{game_config['home_team']['shortn']}_v_{game_config['away_team']['shortn']}_{game_id}")

    if not test:
        title,description,tags=hf.generate_t_d_t(game_config)
        shop_config['image'] = design
        shop_config['title'] = title
        shop_config['description'] =  description
        shop_config['tags'] =  tags
        shop_config['design'] = design
        shop_config['text'] = text
        hf.post(shop_config,publish=True)
    return title

def monday_run(test=False,specific_game = None):
    design_config,shop_config = hf.get_config()
    s3_mover = hf.s3_mover()
    cfbd_loader = hf.cfbp_handler(design_config['cfbd_api'],'09-6-2023')
    yr = dt.date.today().year
    yr=2023

    # refresh teams if new season, could also add something to check if any teams exist
    if hf.new_football_season():
        teams = cfbd_loader.get_team_info()
        s3_mover.pd_to_s3(teams,f'teams/all_teams_{yr}')
    else:
        # get my df of teams
        teams = s3_mover.s3_to_pd(f'teams/all_teams_{yr}')
    
    # get new schedule info and return list of games i need to do
    all_games = cfbd_loader.get_schedule(yr)
    old_games = s3_mover.s3_to_pd(s3_name=f'old/all_games_{yr}')
    to_do_new,to_do_upcoming = cfbd_loader.determine_to_do(old_games)

    if specific_game is not None:
        to_do_new = []
        to_do_upcoming = [specific_game]

    print(f'New games to do {len(to_do_new)}')
    print(f'Upcoming games to do {len(to_do_upcoming)}')

    to_do_upcoming = to_do_upcoming[:10]

    # have to line image path for config up with
    if len(to_do_new)>0:
        print('new games')
        game_weeks = []
        new_game_titles=[]
        for game_id in to_do_new:
            game = all_games.loc[all_games.id == game_id]
            if game.game_type.values[0] == 'regular':
                game_weeks.append(game.week.values[0])
            else: 
                wk = game.game_type.values[0]+str(game.week.values[0])
                game_weeks.append(wk)
            title = process_game(game,teams,design_config,s3_mover,game_id,test,shop_config,pref='post')
            new_game_titles.append(title)
        week = hf.most_frequent(game_weeks)

    if len(to_do_upcoming)>0:
        print('upcoming games')
        game_weeks = []
        to_do_titles = []
        for game_id in to_do_upcoming:
            game = all_games.loc[all_games.id == game_id]
            if game.game_type.values[0] == 'regular':
                game_weeks.append(game.week.values[0])
            else: 
                wk = game.game_type.values[0]+' '+str(game.week.values[0])
                game_weeks.append(wk)
            title = process_game(game,teams,design_config,s3_mover,game_id,test,shop_config,pref='pre')
            to_do_titles.append(title)
        week_upcoming = hf.most_frequent(game_weeks)
    
    if len(to_do_new)>0:
        hf.create_collection(new_game_titles,week,yr,shop_config,pref='post')
    if len(to_do_upcoming)>0:
        hf.create_collection(to_do_titles,week_upcoming,yr,shop_config,pref='pre')
    s3_mover.pd_to_s3(all_games,s3_name=f'old/all_games_{yr}')

if __name__ == "__main__":
    # monday_run(test=False,specific_game=401551788)
    monday_run(test=False)