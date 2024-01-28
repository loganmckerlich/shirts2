import datetime as dt
import helpers as hf





def daily_run(test = False, fake_date=None, limit = None):
    design_config,shop_config = hf.get_config('cbb')
    ify_user = hf.shopify_printify(shop_config,'cbb')
    cfbd_loader = hf.cfbp_handler(design_config['cfbd_api'],fake_date=fake_date)
    if fake_date is not None:
        date = fake_date
    else:
        date = dt.dt.today()
    teams = cfbd_loader.get_team_info()

    todays_games = hf.get_day_bball_games(date)
    yesterdays_games = hf.get_day_bball_games(date-dt.timedelta(days=1))











if __name__ == "__main__":
    # this should fill in mich v uw
    daily_run(test=False,fake_date='01-01-2024',limit=None)
    organize_store('cfb')