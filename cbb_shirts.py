import datetime as dt
import helpers as hf
import time
import traceback
import yaml


def process_game(game, teams, main_config, test, pref, ify_user, save_image):
    game_parsed = hf.parse_cbb_game(game, teams)

    config = hf.combine_configs(main_config, game_parsed)
    design, text = hf.build_cbb(config, test=test)

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
        return title,


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
    created = 0
    with open("info/2024_qualifiers.yml","r") as f:
        qualifiers = yaml.safe_load(f)
    design_config, shop_config = hf.get_config("cbb")
    main_config = hf.combine_configs(design_config, shop_config)
    ify_user = hf.shopify_printify(main_config, "cbb")
    cfbd_loader = hf.cfbp_handler(main_config["cfbd_api"], fake_date=fake_date)
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
                                title = process_game(
                                    game,
                                    teams,
                                    main_config,
                                    test,
                                    pref="pre",
                                    ify_user=ify_user,
                                    save_image=save_image,
                                )
                                print(f"Created {title}, {created} products so far")
                                created +=1
                            else:
                                title = 'na'
                        else:
                            title = process_game(
                                game,
                                teams,
                                main_config,
                                test,
                                pref="pre",
                                ify_user=ify_user,
                                save_image=save_image,
                            )
                            print(f"Created {title}, {created} products so far")
                            created +=1
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
                                title = process_game(
                                    game,
                                    teams,
                                    main_config,
                                    test,
                                    pref="post",
                                    ify_user=ify_user,
                                    save_image=save_image,
                                )
                                print(f"Created {title}, {created} products so far")
                                created +=1
                            else:
                                title = 'na'
                        else:
                            title = process_game(
                                game,
                                teams,
                                main_config,
                                test,
                                pref="post",
                                ify_user=ify_user,
                                save_image=save_image,
                            )
                            print(f"Created {title}, {created} products so far")
                            created +=1
                    except Exception as e:
                        print(f"Failed")
                        print(e)
                        print(traceback.format_exc())
                else:
                    print("skipped because no ranked team and were in that mode")
    print(f"Created {created} new designs. This cost ${(created*4)/100}")
    if created>0:
        ify_user.check_last_endpoint_recur()
        print("5 additional m pause before store organizing")
        time.sleep(60 * 5)
        ify_user.cover_image_wrapper()

        # organize store
        # delete all my collections and rebuild them with all products
        ify_user.reset_collections(teams)


if __name__ == "__main__":
    import pandas as pd
    print("starting")
    with open("info/cbb_runtime_params.yml", "r") as f:
        runtime = yaml.safe_load(f)
    daily_run(
        test=runtime["test"],
        fake_date=pd.to_datetime('2011-03-17'),
        limit=runtime["limit"],
        do_yesterday=runtime["do_yesterday"],
        do_today=runtime["do_today"],
        check_each=True,
        just_ranked=runtime["just_ranked"],
        save_image=runtime["save_image"],
    )

# make it so I dont hit rate limits on my prinitfy post, limit is 200 in 30 m, if im effecient I feel i can be under
    # right now I use 6 (image,image,post,pubish,post,publish) api calls to post one shirt
    # will timeout after 33 shirts
    # when it times out it just stops publishing
# need to run image thing after publishing is complete
# make it so that the whole image switch is better, when posting many shirts theres a larger delay maybe put in a seperate workflow