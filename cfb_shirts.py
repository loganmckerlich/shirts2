import helpers as hf
import datetime as dt
import time


def process_game(game, teams, main_config, test, pref, ify_user):
    game = game.to_dict("records")[0]
    game_config = hf.parse_game(game, teams)
    game_config["game_id"] = game
    config = hf.combine_configs(main_config, game_config)
    design, text = hf.build_cfb(config, test=False)
    if design != "Prompt Failed":
        if design is not None:
            title, description, tags = hf.generate_t_d_t(game_config)
            title = title + " " + pref + "-game"
            main_config["image"] = design
            main_config["title"] = title.title()
            main_config["description"] = description
            main_config["tags"] = tags
            main_config["design"] = design
            main_config["text"] = text
            ify_user.post(publish=True)
        return title


def monday_run(test=False, limit=None, fake_date=None):
    design_config, shop_config = hf.get_config("cfb")
    main_config = hf.combine_configs(design_config, shop_config)
    ify_user = hf.shopify_printify(main_config, "cfb")
    cfbd_loader = hf.cfbp_handler(main_config["cfbd_api"], fake_date=fake_date)
    yr = dt.date.today().year

    # refresh teams
    teams = cfbd_loader.get_team_info()

    # get new schedule info and return list of games i need to do
    all_games = cfbd_loader.get_schedule(yr)

    to_do_new, to_do_upcoming = cfbd_loader.determine_to_do2()

    print(f"New games to do {len(to_do_new)}")
    print(f"Upcoming games to do {len(to_do_upcoming)}")

    if limit is not None:
        print(f"Limiting to {limit} games")
        to_do_upcoming = to_do_upcoming[:limit]
        to_do_new = to_do_new[:limit]

    # have to line image path for config up with
    if len(to_do_new) > 0:
        print("new games")
        for game_id in to_do_new:
            game = all_games.loc[all_games.id == game_id]
            title = process_game(
                game, teams, main_config, test, pref="post", ify_user=ify_user
            )
            print(f"Created {title}")

    if len(to_do_upcoming) > 0:
        print("upcoming games")
        for game_id in to_do_upcoming:
            game = all_games.loc[all_games.id == game_id]
            title = process_game(
                game, teams, main_config, test, pref="pre", ify_user=ify_user
            )
            print(f"Created {title}")


def organize_store(version):
    design_config, shop_config = hf.get_config(version)
    ify_user = hf.shopify_printify(shop_config, version)
    cfbd_loader = hf.cfbp_handler(design_config["cfbd_api"])
    teams = cfbd_loader.get_team_info()

    team_names = list(teams.name)
    # delete all my collections and rebuild them with all products
    ify_user.reset_collections(team_names)


if __name__ == "__main__":
    # this should fill in mich v uw
    monday_run(test=False, fake_date="01-01-2024", limit=None)
    time.sleep(60 * 5)
    organize_store("cfb")
