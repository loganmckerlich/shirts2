import helpers as hf

if __name__ == "__main__":
    design_config,shop_config = hf.get_config('rand')
    ify_user = hf.shopify_printify(shop_config,'rand')
    # ify_user.set_prices(2199)
    # ify_user.delete_all()
    # ify_user.cover_image_wrapper()
    # ify_user.reset_collections(team_names)