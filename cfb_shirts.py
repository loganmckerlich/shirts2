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


class cfb:
    def __init__(
        self,
        test=False,
        fake_date=None,
        limit=None,
        do_upcoming=True,
        do_past=True,
        check_each=False,
        just_ranked=False,
        save_image=True,
        extra_pause=2,
    ):
        self.today_caption = """
            Check out these college football designs. We are designing clothing for every game
            Purchase these designs and more as a shirt ($25.99) or a sweater ($35.99) from the link in my bio
            *
            *
            *
            #CollegeFootball #CFB #GameDayReady
            """

        self.yesterday_caption = """
            Fresh of the press, created these and more designs based off of yesterdays college football schedule!
            Purchase these designs and more as a shirt ($25.99) or a sweater ($35.99) from the link in my bio
            *
            *
            *  
            #CollegeFootball #CFB #GameDayReady
            """

        self.created = 0
        self.test = test
        self.fake_date = fake_date
        self.limit = limit
        self.do_upcoming = do_upcoming
        self.do_past_week = do_past
        self.check_each = check_each
        self.just_ranked = just_ranked
        self.save_image = save_image
        self.extra_pause = extra_pause

        self.today_post_list = []
        self.yesterday_post_list = []


        design_config, shop_config = hf.get_config("cfb")
        self.main_config = hf.combine_configs(design_config, shop_config)
        self.ify_user = hf.shopify_printify(self.main_config, "cfb")
        self.cfbd_loader = hf.cfbp_handler(
            self.main_config["cfbd_api"], fake_date=fake_date
        )
        self.instagram = hf.instagrammer(
            un=self.main_config["instagram"]["username"],
            pw=self.main_config["instagram"]["password"],
            email=self.main_config["instagram"]["eusername"],
            emailpw=self.main_config["instagram"]["epassword"],
        )

        if fake_date is not None:
            date = fake_date
        else:
            date = (dt.datetime.utcnow() + dt.timedelta(hours=-8)).date()
        logger.info(f"Today is {date}")


        # get new schedule info and return list of games i need to do
        self.all_games = self.cfbd_loader.get_schedule(2024)

        self.teams = self.cfbd_loader.get_team_info()
        
        self.past_week, self.upcoming = self.cfbd_loader.determine_to_do3()

        logger.info(f"{len(self.past_week)} games from this past week")
        logger.info(f"{len(self.upcoming)} for games 2 weeks from now")


        if limit is not None:
            logger.info(f"Limiting to {limit} games")
            self.past_week = self.past_week[:limit]
            self.upcoming = self.upcoming[:limit]
        logger.info(f"Cost for dalle api {(len(self.past_week)+len(self.upcoming))*0.04}$, will pause for 15 seconds if you wanna abort")
        time.sleep(15)

    def add_hashtag(self, tag, post):
        if tag is not None:
            tag = tag.replace(' ','').replace('\'','')
            tag = tag+'Football'
            if post == "today":
                self.today_caption = self.today_caption + " #" + tag
            elif post == "yesterday":
                self.yesterday_caption = self.yesterday_caption + " #" + tag


    def process_game(self, game, pref):
        game = game.to_dict("records")[0]
        game_config = hf.parse_game(game, self.teams)
        game_config["game_id"] = game
        if pref == 'pre':
            #remove rankings, we are 2 weeks out so rank could change
            game_config["home_rank"] = None
            game_config["away_rank"] = None
        config = hf.combine_configs(self.main_config, game_config)
        design, text = hf.build_cfb(config, test=self.test)
        if design != "Prompt Failed":
            if design is not None:
                title, description, tags = hf.generate_t_d_t(game_config)
                if pref == "pre":
                    title = title + " pre-game"

                if self.save_image:
                    try:
                        design.save(f".image_saves/cfb/{title}.png")
                    except:
                        logger.warning("couldnt save image")

                self.main_config["image"] = design
                self.main_config["title"] = title.title()
                self.main_config["description"] = description
                self.main_config["tags"] = tags
                self.main_config["design"] = design
                self.main_config["text"] = text
                if not self.test:
                    self.ify_user.post(publish=True)
                    logger.info('Didnt post to shopify/printify bc in test mode')
                self.created += 1
                if self.ify_user.insta_image is not None:
                    if pref == "pre":
                        if (len(self.today_post_list) < 10) & (self.ify_user.insta_image is not None) :
                            # insta_image attribute in ify_user is the image of the most recently createdd item, in this case it should be the sweater
                            self.today_post_list.append(self.ify_user.insta_image)
                            self.add_hashtag(config["home_team"]["shortn"], "today")
                            self.add_hashtag(config["away_team"]["shortn"], "today")
                            self.add_hashtag(config["home_team"]["mascot"], "today")
                            self.add_hashtag(config["away_team"]["mascot"], "today")

                    elif pref == "post":
                        if len(self.yesterday_post_list) < 10:
                            self.yesterday_post_list.append(self.ify_user.insta_image)
                            self.add_hashtag(
                                config["away_team"]["shortn"], "yesterday"
                            )
                            self.add_hashtag(
                                config["home_team"]["shortn"], "yesterday"
                            )
                            self.add_hashtag(config["away_team"]["mascot"], "yesterday")
                            self.add_hashtag(config["home_team"]["mascot"], "yesterday")
            logger.info(f"Created {title}, {self.created} products so far")

    def iterate_games(self, pref, games):
        if len(games) > 0:
            for gameid in games:
                game = self.all_games.loc[self.all_games.id == gameid]
                if (
                    (not self.just_ranked)
                    or (game["home_rank"] is not None)
                    or (game["away_rank"] is not None)
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
        logger.info("about to make some insta posts")
        if len(self.today_post_list) > 0:
            if len(self.today_post_list) == 1:
                self.instagram.single_post(self.today_post_list[0], self.today_caption)
            else:
                self.instagram.carousel_post(self.today_post_list, self.today_caption)

        if len(self.yesterday_post_list) > 0:
            if len(self.yesterday_post_list) == 1:
                self.instagram.single_post(
                    self.yesterday_post_list[0], self.yesterday_caption
                )
            else:
                self.instagram.carousel_post(
                    self.yesterday_post_list, self.yesterday_caption
                )

    def daily_run(self):
        if self.do_past_week:
            self.iterate_games("post", self.past_week)
        if self.do_upcoming:
            self.iterate_games("pre", self.upcoming)
        self.insta_step()

        logger.info(
            f"Created {self.created} new designs. This cost ${(self.created*0.04)}"
        )
        if self.created > 0 and not self.test:
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
                    "College Football T Shirts",
                    "College Football Crewnecks",
                ],
            )

            # this is last cus we waiting on stuff
            self.ify_user.cover_image_wrapper()


if __name__ == "__main__":
    with open("info/cfb_runtime_params.yml", "r") as f:
        runtime = yaml.safe_load(f)
    cbb_obj = cfb(
        test=runtime["test"],
        fake_date=runtime["fake_date"],
        limit=runtime["limit"],
        do_upcoming=runtime["do_upcoming"],
        do_past=runtime["do_past_week"],
        check_each=runtime["check_each"],
        just_ranked=runtime["just_ranked"],
        save_image=runtime["save_image"],
        extra_pause=runtime["extra_pause"],
    )

    cbb_obj.daily_run()
