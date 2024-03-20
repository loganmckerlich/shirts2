import datetime as dt
import helpers as hf
import time
import traceback
import yaml
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger()


class cbb:
    def __init__(
        self,
        test=False,
        fake_date=None,
        limit=None,
        do_yesterday=True,
        do_today=True,
        check_each=False,
        just_ranked=False,
        save_image=True,
        extra_pause=2,
    ):
        self.today_caption = """
            Check out these college basketball designs. We are designing clothing for every game
            Purchase these designs and more as a shirt ($25.99) or a sweater ($35.99) from the link in my bio
            *
            *
            *
            #MarchMadness #CollegeBasketball #NCAABB #GameDayReady
            """

        self.yesterday_caption = """
            Fresh of the press, created these and more designs based off of yesterdays college basketball schedule!
            Purchase these designs and more as a shirt ($25.99) or a sweater ($35.99) from the link in my bio
            *
            *
            *  
            #MarchMadness #CollegeBasketball #NCAABB #GameDayReady
            """

        self.created = 0
        self.test = test
        self.fake_date = fake_date
        self.limit = limit
        self.do_yesterday = do_yesterday
        self.do_today = do_today
        self.check_each = check_each
        self.just_ranked = just_ranked
        self.save_image = save_image
        self.extra_pause = extra_pause

        self.today_post_list = []
        self.yesterday_post_list = []
        self.created = 0
        with open("info/2024_qualifiers.yml", "r") as f:
            self.qualifiers = yaml.safe_load(f)
        design_config, shop_config = hf.get_config("cbb")
        self.main_config = hf.combine_configs(design_config, shop_config)
        self.ify_user = hf.shopify_printify(self.main_config, "cbb")
        self.cfbd_loader = hf.cfbp_handler(
            self.main_config["cfbd_api"], fake_date=fake_date
        )

        if fake_date is not None:
            date = fake_date
        else:
            date = (dt.datetime.utcnow() + dt.timedelta(hours=-8)).date()
        logger.info(f"Today is {date}")

        self.teams = self.cfbd_loader.get_team_info()
        if do_today:
            self.todays_games = hf.get_day_bball_games(date)
            logger.info(f"{len(self.todays_games)} Games Today")
        if do_yesterday:
            self.yesterdays_games = hf.get_day_bball_games(date - dt.timedelta(days=1))
            logger.info(f"{len(self.yesterdays_games)} Games Yesterday")

        if limit is not None:
            logger.info(f"Limiting to {limit} games")
            self.todays_games = self.todays_games[:limit]
            self.yesterdays_games = self.yesterdays_games[:limit]

    def add_hashtag(self, tag, post):
        if tag is not None:
            tag = tag.replace(' ','').replace('\'','')
            #WashingtonBasketball
            #HuskiesBasketball
            tag = tag+'Basketball'
            if post == "today":
                self.today_caption = self.today_caption + " #" + tag
            elif post == "yesterday":
                self.yesterday_caption = self.yesterday_caption + " #" + tag

    def process_game(self, game, pref):
        game_parsed = hf.parse_cbb_game(game, self.teams)

        config = hf.combine_configs(self.main_config, game_parsed)
        design, text = hf.build_cbb(config, test=self.test)

        if design != "prompt failed":
            if design is not None:
                title, description, tags = hf.generate_t_d_t_cbb(game_parsed)
                if pref == "pre":
                    title = title + " pre-game"

                if self.save_image:
                    try:
                        design.save(f".image_saves/{title}.png")
                    except:
                        logger.warning("couldnt save image")
                self.main_config["image"] = design
                self.main_config["title"] = title.title()
                self.main_config["description"] = description
                self.main_config["tags"] = tags
                self.main_config["design"] = design
                self.main_config["text"] = text
                self.ify_user.post(publish=True)
                self.created += 1
                if self.ify_user.insta_image is not None:
                    if pref == "pre":
                        if (len(self.today_post_list) < 10) & (self.ify_user.insta_image is not None) :
                            # insta_image attribute in ify_user is the image of the most recently createdd item, in this case it should be the sweater
                            self.today_post_list.append(self.ify_user.insta_image)
                            self.add_hashtag(config["team2"]["name"], "today")
                            self.add_hashtag(config["team1"]["name"], "today")
                            self.add_hashtag(config["team2"]["mascot"], "today")
                            self.add_hashtag(config["team1"]["mascot"], "today")

                    elif pref == "post":
                        if len(self.yesterday_post_list) < 10:
                            self.yesterday_post_list.append(self.ify_user.insta_image)
                            self.add_hashtag(
                                config["team2"]["name"], "yesterday"
                            )
                            self.add_hashtag(
                                config["team1"]["name"], "yesterday"
                            )
                            self.add_hashtag(config["team2"]["mascot"], "yesterday")
                            self.add_hashtag(config["team1"]["mascot"], "yesterday")
            logger.info(f"Created {title}, {self.created} products so far")

    def iterate_games(self, pref, games):
        if len(games) > 0:
            for i in range(len(games)):
                game = games.iloc[i]
                if (
                    (not self.just_ranked)
                    or (game["team1Rank"] is not None)
                    or (game["team2Rank"] is not None)
                    or (game["team1"] in self.qualifiers)
                    or (game["team2"] in self.qualifiers)

                ):
                    try:
                        if self.check_each:
                            logger.info(game)
                            a = input("proceed?")
                            if a == "yes":
                                self.process_game(game, pref)
                        else:
                            self.process_game(game, pref)
                    except Exception as e:
                        logger.info(f"Failed")
                        logger.warning(e, exc_info=True)
                else:
                    logger.info("skipped because no ranked team and were in that mode")

    def insta_step(self):
        instagram = hf.instagrammer(
            un=self.main_config["instagram"]["username"],
            pw=self.main_config["instagram"]["password"],
            email=self.main_config["instagram"]["eusername"],
            emailpw=self.main_config["instagram"]["epassword"],
        )
        logger.info("about to make some insta posts")
        if len(self.today_post_list) > 0:
            if len(self.today_post_list) == 1:
                instagram.single_post(self.today_post_list[0], self.today_caption)
            else:
                instagram.carousel_post(self.today_post_list, self.today_caption)

        if len(self.yesterday_post_list) > 0:
            if len(self.yesterday_post_list) == 1:
                instagram.single_post(
                    self.yesterday_post_list[0], self.yesterday_caption
                )
            else:
                instagram.carousel_post(
                    self.yesterday_post_list, self.yesterday_caption
                )

    def daily_run(self):
        if self.do_today:
            self.iterate_games("pre", self.todays_games)
        if self.do_yesterday:
            self.iterate_games("post", self.yesterdays_games)

        try:
            self.insta_step()
        except:
            logger.warning("insta step failed", exc_info = True)

        logger.info(
            f"Created {self.created} new designs. This cost ${(self.created*4)/100}"
        )
        if self.created > 0:
            logger.info("Waiting to see most recent product as published")
            self.ify_user.check_last_endpoint_recur()

            logger.info(
                f"{self.extra_pause} additional m pause before store organizing"
            )
            time.sleep(60 * self.extra_pause)

            # organize store
            # delete all my collections and rebuild them with all products
            self.ify_user.reset_collections(
                self.teams,
                exclude=[
                    "All Products",
                    "College Basketball T Shirts",
                    "College Basketball Crewnecks",
                ],
            )

            # this is last cus we waiting on stuff
            self.ify_user.cover_image_wrapper()


if __name__ == "__main__":
    with open("info/cbb_runtime_params.yml", "r") as f:
        runtime = yaml.safe_load(f)
    cbb_obj = cbb(
        test=runtime["test"],
        fake_date=runtime["fake_date"],
        limit=runtime["limit"],
        do_yesterday=runtime["do_yesterday"],
        do_today=runtime["do_today"],
        check_each=runtime["check_each"],
        just_ranked=runtime["just_ranked"],
        save_image=runtime["save_image"],
        extra_pause=runtime["extra_pause"],
    )

    cbb_obj.daily_run()
