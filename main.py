import datetime as dt
import helpers as hf
# warnings.filterwarnings("ignore", category=DeprecationWarning) 



def process_game(game,teams,design_config,s3_mover,game_id,test,shop_config,pref):
    print(f'    generating game image')
    game = game.to_dict('records')
    game_config = hf.parse_game(game,teams)
    game_config['game_id'] = game
    config = hf.combine_configs(design_config,game_config)
    design = hf.build_design(config,test=False)

    # do I need to save all my images to s3?
    s3_mover.image_to_s3(design,rf"{pref}/{game_config['home_team']['shortn']}_v_{game_config['away_team']['shortn']}_{game_id}.csv")

    if not test:
        title,description,tags=hf.generate_t_d_t(game_config)
        shop_config['image'] = design
        shop_config['title'] = title
        shop_config['description'] =  description
        shop_config['tags'] =  tags
        shop_config['image'] = design
        hf.post(shop_config)
def monday_run(test=False):
    design_config,shop_config = hf.get_config()
    cfbd_loader = hf.cfbp_handler(design_config['cfbd_api'])
    s3_mover = hf.s3_mover()
    yr = dt.date.today().year

    # refresh teams if new season, could also add something to check if any teams exist
    if hf.new_football_season():
        teams = cfbd_loader.get_team_info()
        s3_mover.pd_to_s3(teams,f'teams/all_teams_{yr}')
    else:
        # get my df of teams
        teams = s3_mover.s3_to_pd(f'teams/all_teams_{yr}')
    
    # get new schedule info and return list of games i need to do
    to_do_new,to_do_upcoming,all_games = cfbd_loader.get_schedule(yr)

    print(f'New games to do {len(to_do_new)}')
    print(f'Upcoming games to do {len(to_do_upcoming)}')

    # have to line image path for config up with
    print('new games')
    for game_id in to_do_new:
        game = all_games.loc[all_games.id == game_id]
        process_game(game,teams,design_config,s3_mover,game_id,test,shop_config,pref='post')

    print('upcoming games')
    for game_id in to_do_upcoming:
        game = all_games.loc[all_games.id == game_id]
        process_game(game,teams,design_config,s3_mover,game_id,test,shop_config,pref='pre')

if __name__ == "__name__":
    monday_run()