import helpers as hf

if __name__ == "__main__":
    design_config, shop_config = hf.get_config("cbb")
    main_config = hf.combine_configs(design_config, shop_config)
    ify_user = hf.shopify_printify(main_config, "cbb")
    cfbd_loader = hf.cfbp_handler(main_config["cfbd_api"])
    teams = cfbd_loader.get_team_info()

    # ify_user.set_prices(2199)
    # ify_user.cover_image_wrapper()
    ify_user.reset_collections(teams)
    # ify_user.delete_collections()
    # ify_user.create_collections_cbb(teams)
