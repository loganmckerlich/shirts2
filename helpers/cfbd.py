import cfbd
import pandas as pd
import numpy as np
import ast

class cfbp_handler():

    def config(self):
        configuration = cfbd.Configuration()
        configuration.api_key['Authorization'] = self.key
        configuration.api_key_prefix['Authorization'] = 'Bearer'
        self.configuration = configuration

    def __init__(self, key):
        self.key=key
        self.config()

    def get_team_info(self):
        # this would run daily to add scores as they come
        cfbd_instance =cfbd.TeamsApi(cfbd.ApiClient(self.configuration))

        cfbd_response = cfbd_instance.get_teams()

        all_team_info=[]
        for team in cfbd_response:
            team_id=team.id
            name=team.school.replace(')','').replace('(','')
            abrev=team.abbreviation
            color=team.color
            alt_color=team.alt_color
            mascot=team.mascot
            if type(team.logos)!=list:
                # this means no logo
                logos= r'https://github.com/klunn91/team-logos/blob/master/NCAA/_NCAA_logo.png?raw=true'
            else:
                logos = ast.literal_eval(str(team.logos))[0]

            team_info = [team_id,name,abrev,color,alt_color,mascot,logos]
            all_team_info.append(team_info)

        all_teams_df = pd.DataFrame(all_team_info,columns = ['id','name','abrev','color','alt_color','mascot','logos']).sort_values('name')
        all_teams_df.color = np.where(all_teams_df.color.isna(),'#FFFFFF',all_teams_df.color)
        all_teams_df.to_csv(f'./all_teams.csv')

    def get_schedule(self,year):
        # this would run daily to add scores as they come
        cfbd_instance = cfbd.GamesApi(cfbd.ApiClient(self.configuration))
        cfbd_response = cfbd_instance.get_games(year=2023,season_type='both')

        all_game_info=[]
        for game in cfbd_response:
            htid=game.home_id
            home_team=game.home_team.replace(')','').replace('(','')
            home_points=game.home_points
            atid=game.away_id
            away_team=game.away_team.replace(')','').replace('(','')
            away_points=game.away_points
            game_date=game.start_date
            complete=game.completed
            game_info = [htid,home_team,home_points,atid,away_team,away_points,game_date,complete]
            all_game_info.append(game_info)

        all_games_df = pd.DataFrame(all_game_info,columns = ['home_id','home','home_score','away_id','away','away_score','startdate','complete']).sort_values('startdate')
        all_games_df=all_games_df.drop_duplicates()
        all_games_df.to_csv(f'all_games_{year}.csv')