from bs4 import BeautifulSoup
import datetime as dt
import requests
import pandas as pd

def get_day_bball_games(date_=dt.date.today()-dt.timedelta(days=1)):
    y,d,m = date_.year,date_.day,date_.month
    base_url = f'https://www.sports-reference.com/cbb/boxscores/index.cgi?month={m}&day={d}&year={y}'
    res = requests.get(base_url, headers={'User-Agent': 'Mozilla/5.0'})
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    games = soup.find_all("div", {"class": "game_summary nohover gender-m"})
    game_rows=[]
    for game in games:
        team2 = game.findAll('tr')[0]
        try:
            team2_rank = team2.findChildren('td')[0].find('span').get_text(strip=True)
        except:
            team2_rank=None
        team2_team = team2.findChildren('td')[0].find('a').get_text(strip=True)
        try:
            team2_score = int(team2.findChildren('td')[1].get_text(strip=True))
        except:
            team2_score=None


        team1 = game.findAll('tr')[1]
        try:
            team1_rank = team1.findChildren('td')[0].find('span').get_text(strip=True)
        except:
            team1_rank=None
        team1_team = team1.findChildren('td')[0].find('a').get_text(strip=True)

        try:
            team1_score = int(team1.findChildren('td')[1].get_text(strip=True))
        except:
            team1_score=None

        desc = game.findChildren('tr')[-1].get_text(strip=True).replace('Tourn.','Tournament')
        if 'Tourn' not in desc:
            #only care about tournament descriptions
            desc=None

        game_rows.append([date_,team1_team,team1_rank,team1_score,
                      team2_team,team2_rank,team2_score,
                      desc])
        
    return pd.DataFrame(game_rows,columns = ['date_','team1','team1Rank','team1Score','team2','team2Rank','team2Score','Desc'])
