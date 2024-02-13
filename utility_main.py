import helpers as hf

if __name__ == "__main__":
    design_config, shop_config = hf.get_config("cbb")
    ify_user = hf.shopify_printify(shop_config, "cbb")
    main_config = hf.combine_configs(design_config, shop_config)
    cfbd_loader = hf.cfbp_handler(main_config["cfbd_api"])
    teams = cfbd_loader.get_team_info()
    team_names = list(teams.name)

    # ify_user.set_prices(2199)
    # ify_user.delete_all()
    # ify_user.cover_image_wrapper()
    ify_user.reset_collections(team_names)
