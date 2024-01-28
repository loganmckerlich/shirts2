import cfbd
import pandas as pd
import numpy as np
import ast
import datetime as dt
import math


class cfbp_handler:
    def config(self):
        configuration = cfbd.Configuration()
        configuration.api_key["Authorization"] = self.key
        configuration.api_key_prefix["Authorization"] = "Bearer"
        self.configuration = configuration

    def __init__(self, key, fake_date=None):
        self.key = key
        self.fake_date = fake_date
        self.config()

    def get_team_info(self):
        # this would run daily to add scores as they come
        # note this is more than just fbs teams, for games where an fbs plays a non fbs we need both
        cfbd_instance = cfbd.TeamsApi(cfbd.ApiClient(self.configuration))

        cfbd_response = cfbd_instance.get_teams()

        all_team_info = []
        for team in cfbd_response:
            # some schools are in cfbd with minimal data, but i want more for cbb
            if team.school.lower() not in ['gonzaga']:
                team_id = team.id
                name = team.school.replace(")", "").replace("(", "")
                long_name = team.alt_name_3
                abrev = team.abbreviation
                color = team.color
                alt_color = team.alt_color
                mascot = team.mascot
                division = team.classification
                if type(team.logos) != list:
                    # this means no logo
                    logos = "https://github.com/klunn91/team-logos/blob/master/NCAA/_NCAA_logo.png?raw=true"
                else:
                    logos = ast.literal_eval(str(team.logos))[0]

                team_info = [team_id, name, abrev, color, alt_color, mascot, logos, division,long_name]
                all_team_info.append(team_info)
        
        # additional schools that are cbb but not cfb, manually add some big ones
        uconn = [np.nan,"Uconn","UCONN","#000E2F",None,"Huskies","https://1000logos.net/wp-content/uploads/2017/08/uconn-huskies-logo.png",None,None]
        zags = [np.nan,"Gonzaga","GU","#041E42",None,"Bulldogs","https://static.wixstatic.com/media/7383ad_b5ee32ef2d4340d4822c1a448e961518~mv2_d_1500_1500_s_2.png/v1/fill/w_1500,h_1500,al_c/Gonzaga.png",None,None]
        all_team_info.append(uconn)
        all_team_info.append(zags)
        all_teams_df = pd.DataFrame(
            all_team_info,
            columns=["id", "name", "abrev", "color", "alt_color", "mascot", "logos", "division", "long_name"],
        ).sort_values("name")
        all_teams_df.color = np.where(
            all_teams_df.color.isna(), "#FFFFFF", all_teams_df.color
        )
        self.teams = all_teams_df
        return all_teams_df

    def determine_to_do2(self):
        new_games = self.all_games
        if self.fake_date is not None:
            print("artificially setting to monday past date")
            today = pd.to_datetime(self.fake_date)
        else:
            today = dt.date.today()

        games_this_past_week = new_games.loc[pd.to_datetime(new_games.monday) == pd.to_datetime(today)-pd.Timedelta(weeks=1)]

        # this mon represents all games in coming week, next mon is 2 weeks out games
        games_2_weeks_out = new_games.loc[pd.to_datetime(new_games.monday) == pd.to_datetime(today)+pd.Timedelta(weeks=1)]

        new_games = list(games_this_past_week.id)
        upcoming_games = list(games_2_weeks_out.id)

        return new_games,upcoming_games

    def get_schedule(self, year):
        # this would run daily to add scores as they come
        cfbd_instance = cfbd.GamesApi(cfbd.ApiClient(self.configuration))
        cfbd_response = cfbd_instance.get_games(year=year, season_type="both")

        all_game_info = []
        for game in cfbd_response:
            if game.home_division == 'fbs' or game.away_division == 'fbs':
                game_id = game.id
                htid = game.home_id
                home_team = game.home_team.replace(")", "").replace("(", "")
                home_points = game.home_points
                atid = game.away_id
                away_team = game.away_team.replace(")", "").replace("(", "")
                away_points = game.away_points
                game_date = game.start_date
                game_week = game.week
                complete = game.completed
                game_type = game.season_type
                game_info = [
                    game_id,
                    htid,
                    home_team,
                    home_points,
                    atid,
                    away_team,
                    away_points,
                    game_date,
                    game_week,
                    complete,
                    game_type,
                ]
                all_game_info.append(game_info)

        all_games_df = pd.DataFrame(
            all_game_info,
            columns=[
                "id",
                "home_id",
                "home",
                "home_score",
                "away_id",
                "away",
                "away_score",
                "startdate",
                "week",
                "complete",
                "game_type",
            ],
        ).sort_values("startdate")
        all_games_df.startdate = pd.to_datetime(all_games_df.startdate)
        all_games_df = all_games_df.drop_duplicates()
        all_games_df['monday'] = all_games_df['startdate'] - all_games_df['startdate'].dt.weekday.astype('timedelta64[D]')
        all_games_df.monday = all_games_df.monday.apply(lambda x:x.date())
        all_games_df.startdate = all_games_df.startdate.apply(lambda x:x.date())
        all_games_df.game_type = np.where(all_games_df.game_type=='regular', 'regular-season',all_games_df.game_type)
        all_games_df.week = all_games_df['game_type']+' Week '+all_games_df['week'].astype(str)

        self.all_games = all_games_df
        return all_games_df
