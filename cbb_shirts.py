import datetime as dt
import helpers as hf
import time
import traceback
import yaml

def process_game(game, teams, main_config, test, pref, ify_user, save_image, post_list):
    game_parsed = hf.parse_cbb_game(game, teams)

    config = hf.combine_configs(main_config, game_parsed)
    design, text = hf.build_cbb(config, test=test)
    if len(post_list)<10:
        post_list.append(design)

    if design != "prompt failed":
        if design is not None:
            title, description, tags = hf.generate_t_d_t_cbb(game_parsed)
            if pref == "pre":
                title = title + " pre-game"

            if save_image:
                try:
                    design.save(f".image_saves/{title}.png")
                except:
                    print("couldnt save image")
            main_config["image"] = design
            main_config["title"] = title.title()
            main_config["description"] = description
            main_config["tags"] = tags
            main_config["design"] = design
            main_config["text"] = text
            ify_user.post(publish=True)
        return title, post_list


def daily_run(
    test=False,
    fake_date=None,
    limit=None,
    do_yesterday=True,
    do_today=True,
    check_each=False,
    just_ranked=False,
    save_image=True,
):
    today_caption = """
    Check out these college basketball designs. We are designing clothing for every game
    Purchase these designs and more as a shirt ($25.99) or a sweater ($35.99) from the link in my bio
    *
    *
    *
    #MarchMadness #CollegeBasketball #NCAABB #BallIsLife #SupportLocal #ShopSmall #SmallBizLove #StudentAthlete #HoopsCulture
    #GameDayReady #BasketballDreams #ShopLocalWinBig #HustleAndFlow #NCAATourney #SmallBizCommunity #DunkDreams #NetProfit
    #BasketballBiz #LocalGameGlobalDreams #BasketballNation #ChampionMindset #SportsClothing      
    """

    yesterday_caption = """
    Fresh of the press, created these and more designs based off of yesterdays college basketball schedule!
    Purchase these designs and more as a shirt ($25.99) or a sweater ($35.99) from the link in my bio
    *
    *
    *
    #MarchMadness #CollegeBasketball #NCAABB #BallIsLife #SupportLocal #ShopSmall #SmallBizLove #StudentAthlete #HoopsCulture
    #GameDayReady #BasketballDreams #ShopLocalWinBig #HustleAndFlow #NCAATourney #SmallBizCommunity #DunkDreams #NetProfit
    #BasketballBiz #LocalGameGlobalDreams #BasketballNation #ChampionMindset #SportsClothing      
    """
    today_post_list=[]
    yesterday_post_list=[]
    created = 0
    with open("info/2024_qualifiers.yml", "r") as f:
        qualifiers = yaml.safe_load(f)
    design_config, shop_config = hf.get_config("cbb")
    main_config = hf.combine_configs(design_config, shop_config)
    ify_user = hf.shopify_printify(main_config, "cbb")
    cfbd_loader = hf.cfbp_handler(main_config["cfbd_api"], fake_date=fake_date)
    instagram = hf.instagrammer(un = main_config["instagram"]["username"], pw = main_config["instagram"]["password"])

    if fake_date is not None:
        date = fake_date
    else:
        date = (dt.datetime.utcnow() + dt.timedelta(hours=-8)).date()
    print(f"Today is {date}")
    teams = cfbd_loader.get_team_info()

    todays_games = hf.get_day_bball_games(date)
    yesterdays_games = hf.get_day_bball_games(date - dt.timedelta(days=1))

    print(f"{len(todays_games)} Games Today")
    print(f"{len(yesterdays_games)} Games Yesterday")
    if limit is not None:
        print(f"Limiting to {limit} games")
        todays_games = todays_games[:limit]
        yesterdays_games = yesterdays_games[:limit]
    if do_today:
        if len(todays_games) > 0:
            for i in range(len(todays_games)):
                game = todays_games.iloc[i]
                if (
                    (not just_ranked)
                    or (game["team1Rank"] is not None)
                    or (game["team2Rank"] is not None)
                    or (game["team1"] in qualifiers)
                    or (game["team2"] in qualifiers)
                ):
                    try:
                        if check_each:
                            print(game)
                            a = input("proceed?")
                            if a == "yes":
                                title,today_post_list = process_game(
                                    game,
                                    teams,
                                    main_config,
                                    test,
                                    pref="pre",
                                    ify_user=ify_user,
                                    save_image=save_image,
                                    post_list=today_post_list
                                )
                                created += 1
                                print(f"Created {title}, {created} products so far")
                            else:
                                title = "na"
                        else:
                            title,today_post_list = process_game(
                                game,
                                teams,
                                main_config,
                                test,
                                pref="pre",
                                ify_user=ify_user,
                                save_image=save_image,
                                post_list=today_post_list
                            )
                            created += 1
                            print(f"Created {title}, {created} products so far")
                    except Exception as e:
                        print(f"Failed")
                        print(e)
                        print(traceback.format_exc())
                else:
                    print("skipped because no ranked team and were in that mode")
            
    if do_yesterday:
        if len(yesterdays_games) > 0:
            for i in range(len(yesterdays_games)):
                game = yesterdays_games.iloc[i]
                if (
                    (not just_ranked)
                    or (game["team1Rank"] is not None)
                    or (game["team2Rank"] is not None)
                    or (game["team1"] in qualifiers)
                    or (game["team2"] in qualifiers)
                ):
                    try:
                        if check_each:
                            print(game)
                            a = input("proceed?")
                            if a == "yes":
                                title,yesterday_post_list = process_game(
                                    game,
                                    teams,
                                    main_config,
                                    test,
                                    pref="post",
                                    ify_user=ify_user,
                                    save_image=save_image,
                                    post_list=yesterday_post_list
                                )
                                created += 1
                                print(f"Created {title}, {created} products so far")
                            else:
                                title = "na"
                        else:
                            title,yesterday_post_list = process_game(
                                game,
                                teams,
                                main_config,
                                test,
                                pref="post",
                                ify_user=ify_user,
                                save_image=save_image,
                                post_list=yesterday_post_list
                            )
                            created += 1
                            print(f"Created {title}, {created} products so far")
                    except Exception as e:
                        print(f"Failed")
                        print(e)
                        print(traceback.format_exc())
                else:
                    print("skipped because no ranked team and were in that mode")

    print(f"Created {created} new designs. This cost ${(created*4)/100}")
    if created > 0:
        print('Waiting to see most recent product as published')
        ify_user.check_last_endpoint_recur()

        print("about to make some insta posts")
        if len(today_post_list)>0:
            if len(today_post_list)==1:
                instagram.single_post(today_post_list[0],today_caption)
            else:
                instagram.carousel_post(today_post_list,today_caption)
        
        if len(yesterday_post_list)>0:
            if len(today_post_list)==1:
                instagram.single_post(today_post_list[0],yesterday_caption)
            else:
                instagram.carousel_post(today_post_list,yesterday_caption)

        print("5 additional m pause before store organizing")
        time.sleep(60 * 5)

        # organize store
        # delete all my collections and rebuild them with all products
        ify_user.reset_collections(
            teams,
            exclude=[
                "All Products",
                "College Basketball T Shirts",
                "College Basketball Crewnecks",
            ],
        )

        # this is last cus we waiting on stuff
        ify_user.cover_image_wrapper()


if __name__ == "__main__":
    print("starting")
    with open("info/cbb_runtime_params.yml", "r") as f:
        runtime = yaml.safe_load(f)
    daily_run(
        test=runtime["test"],
        fake_date=runtime['fake_date'],
        limit=runtime["limit"],
        do_yesterday=runtime["do_yesterday"],
        do_today=runtime["do_today"],
        check_each=runtime['check_each'],
        just_ranked=runtime["just_ranked"],
        save_image=runtime["save_image"],
    )
