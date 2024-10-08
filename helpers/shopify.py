import requests
import base64
from io import BytesIO
import json
import time
import datetime as dt
import pandas as pd
from PIL import Image
import logging

logger = logging.getLogger()


class shopify_printify:
    def __init__(self, post_dict, version):
        self.insta_image = None
        self.post_dict = post_dict
        self.headers_printify = {
            "Authorization": f"Bearer {post_dict['printify_access']}",
            "Content-Type": "application/json",
        }
        self.headers_shopify = {
            "X-Shopify-Access-Token": post_dict["shopify_access"],
            "Content-Type": "application/json",
        }
        self.version = version
        self.big_body = """
            {
            product(id:"gid://shopify/Product/prod_id") {
                title
                media(first:5) {
                edges {
                    node {
                    ... fieldsForMediaTypes
                    }
                }
                }
            }
            }

            fragment fieldsForMediaTypes on Media {
            alt
            mediaContentType
            preview {
                image {
                id
                altText
                url
                }
            }
            status
            ... on Video {
                id
                sources {
                format
                height
                mimeType
                url
                width
                }
                originalSource {
                format
                height
                mimeType
                url
                width
                }
            }
            ... on ExternalVideo {
                id
                host
                embeddedUrl
            }
            ... on Model3d {
                sources {
                format
                mimeType
                url
                }
                originalSource {
                format
                mimeType
                url
                }
            }
            ... on MediaImage {
                id
                image {
                altText
                url
                }
            }
            }
            """

    def post(self, publish=False):
        upload_url = f"{self.post_dict['base_url']}/uploads/images.json"
        product_url = f"{self.post_dict['base_url']}/shops/{self.post_dict[self.version]['shop_id']}/products.json"

        # this posts a design, but doesnt publish it
        buffered = BytesIO()
        self.post_dict["design"].save(buffered, format="png")
        img = base64.b64encode(buffered.getvalue()).decode("utf-8")

        # Upload the image to the Printify media library
        data = {"file_name": self.post_dict["title"], "contents": img}
        img_response = requests.post(
            upload_url, headers=self.headers_printify, json=data
        )

        buffered = BytesIO()
        self.post_dict["text"].save(buffered, format="png")
        txt = base64.b64encode(buffered.getvalue()).decode("utf-8")

        data = {"file_name": self.post_dict["title"] + "txt", "contents": txt}
        txt_response = requests.post(
            upload_url, headers=self.headers_printify, json=data
        )

        if img_response.status_code == 200 and txt_response.status_code == 200:
            logger.info("image and text sent to printify")
            image_id = img_response.json()["id"]
            text_id = txt_response.json()["id"]

            for product_type in self.post_dict["products"]:
                logger.info(f"doing {product_type['name']}")
                variants = [
                    {"id": id, "price": product_type["price"], "is_enabled": True}
                    for id in product_type["variant_ids"]
                ]
                if product_type["name"] == "sweater":
                    descrip = self.post_dict["description"].replace("shirt", "crewneck")
                else:
                    descrip = self.post_dict["description"]
                data = {
                    "title": self.post_dict["title"],
                    "description": descrip,
                    "tags": self.post_dict["tags"].split(
                        ", "
                    ),  # Assuming tags are comma-separated in the CSV
                    "blueprint_id": product_type["blueprint_id"],
                    "print_provider_id": product_type["print_provider_id"],
                    "variants": variants,
                    "print_areas": [
                        {
                            "variant_ids": product_type["variant_ids"],
                            "placeholders": [
                                {
                                    "position": "back",  # post to back of shirt, put a lil one on front with just date team score
                                    "images": [
                                        {
                                            "id": image_id,
                                            "x": 0.5,
                                            "y": 0.5,
                                            "scale": 1,
                                            "angle": 0,
                                        }
                                    ],
                                },
                                {
                                    "position": "front",
                                    "images": [
                                        {
                                            "id": text_id,
                                            "x": 0.25,
                                            "y": 0.25,
                                            "scale": 0.4,
                                            "angle": 0,
                                        }
                                    ],
                                },
                            ],
                        }
                    ],
                }

                response1 = requests.post(
                    product_url, headers=self.headers_printify, json=data
                )
                if response1.status_code == 200:
                    logger.info("Product posted successfully in Printify")
                else:
                    logger.warning("Failed to post product in Printify")
                    logger.warning(response1.text)
                    logger.warning(response1.status_code)
                if product_type["name"] == "sweater":
                    try:
                        # the image at index 1 (in printify) is the back of the sweater
                        insta_image = json.loads(response1.text)["images"][1]["src"]
                        ii_response = requests.get(insta_image)
                        self.insta_image = Image.open(BytesIO(ii_response.content))
                    except:
                        logger.warning(
                            f"failed to get instagram image url, URL: {insta_image}"
                        )
                        self.insta_image = None

                if publish:
                    # limited to posting one product per api post
                    # I think I can add a step maybe just before publishing to edit which photos it publishes
                    # this part does the publishing
                    printify_publish = f"{self.post_dict['base_url']}/shops/{self.post_dict[self.version]['shop_id']}/products/{json.loads(response1.text)['id']}/publish.json"

                    update_data = {
                        "title": True,
                        "description": True,
                        "images": True,
                        "variants": True,
                        "tags": True,
                        "keyFeatures": True,
                        "shipping_template": True,
                    }

                    # Patch request to update the product status
                    response2 = requests.post(
                        printify_publish,
                        headers=self.headers_printify,
                        json=update_data,
                    )

                    if response2.status_code == 200:
                        logger.info("Product published successfully in Printify")
                        # commenting this out because more effecient to just hit rate limit then wait
                        # if response2.headers["X-RateLimit-Remaining"] < 3 :
                        #     # hopefully its a window thing and in a minute, the couple I started with arent included
                        #     logger.warning("Approaching rate limit, pausing for a minute")
                        #     time.sleep(60)
                    elif response2.status_code == 429:
                        logger.warning(
                            f"timed out, will sleep until window resets {response2.headers['X-RateLimit-Reset']} seconds"
                        )
                        time.sleep(int(response2.headers["X-RateLimit-Reset"]))
                        response2 = requests.post(
                            printify_publish,
                            headers=self.headers_printify,
                            json=update_data,
                        )
                        if response2.status_code == 200:
                            logger.info("Product published successfully in Printify")
                        else:
                            logger.warning(
                                "Failed to publish because of rate limit, waited for api window to reset, failed again"
                            )
                            logger.warning(response2.status_code)
                            logger.warning(response2.text)
                    else:
                        logger.warning(
                            "Failed to publish product in Printify for some reason other than rate limit"
                        )
                        logger.warning(response2.status_code)
                        logger.warning(response2.text)

            self.last_endpoint = f"{self.post_dict['base_url']}/shops/{self.post_dict[self.version]['shop_id']}/products/{json.loads(response1.text)['id']}.json"

        else:
            logger.warning("unable to send image to printify")
            logger.warning(img_response.status_code)
            logger.warning(img_response.text)

    def check_last_endpoint_recur(self):
        # this checks if my last published product is done publishing yet
        url = self.last_endpoint
        response = requests.get(url=url, headers=self.headers_printify)
        if (
            "external" in json.loads(response.text).keys()
            and json.loads(response.text)["external"]["id"] != ""
        ):
            logger.info("Last Product is published")
            return True
        else:
            # wait 25 secs then check again
            time.sleep(25)
            return self.check_last_endpoint_recur()

    def update_images2(self, prods, title=None):
        if title is None:
            title = [None] * len(prods)
        # this reorders images once in shopify
        for prod, team in zip(prods, title):
            logger.info(f"Attempting to swap image for {team}")
            try:
                prod_id = prod["id"]
                prod_gql = prod["admin_graphql_api_id"]
                body = self.big_body.replace("prod_id", str(prod_id))
                # now that I have the images I can reorder them
                url = f"https://{self.post_dict[self.version]['shop_name']}.myshopify.com/admin/api/2024-01/graphql.json"
                # from this response i can get my images
                response = requests.post(
                    url=url, headers=self.headers_shopify, json={"query": body}
                )

                images = json.loads(response.text)["data"]["product"]["media"]["edges"]
                # could I get an image url out of this and use that for insta post?
                image0 = images[0]["node"]["id"]
                image2 = images[2]["node"]["id"]

                q = (
                    """
                mutation reorderProductMedia {
                    productReorderMedia(
                    id: "gidp",
                    moves: [
                    {
                        id: "gid0",
                        newPosition: "2"
                    },
                    {
                        id: "gid2",
                        newPosition: "0"
                    }
                    ]) {
                    job {
                        id
                        done
                    }
                    mediaUserErrors {
                        code
                        field
                        message
                    }
                    }
                }
                """.replace(
                        "gidp", prod_gql
                    )
                    .replace("gid0", image0)
                    .replace("gid2", image2)
                )

                graphql_url = f"https://{self.post_dict[self.version]['shop_name']}.myshopify.com/admin/api/2023-04/graphql.json"

                response = requests.post(
                    graphql_url, headers=self.headers_shopify, json={"query": q}
                )
                if response.status_code == 200:
                    logger.info("Image swapped")

                # This is a better usage of gql
                alt_text_query = "mutation productUpdateMedia($media: [UpdateMediaInput!]!, $productId: ID!) { productUpdateMedia(media: $media, productId: $productId) { media { alt } } }"

                alt_text_var = {
                    "media": [
                        {"alt": team + " back view", "id": image2},
                        {"alt": team + " front view", "id": image0},
                    ],
                    "productId": prod_gql,
                }

                alt_resp = requests.post(
                    graphql_url,
                    headers=self.headers_shopify,
                    json={"query": alt_text_query, "variables": alt_text_var},
                )
                if alt_resp.status_code == 200:
                    logger.info("Set alt text")
                elif alt_resp.status_code != 200:
                    logger.warning(f"Failed to add alt text")
                    logger.warning(alt_resp.status_code)
                    logger.warning(alt_resp.text)

                if (
                    json.loads(alt_resp.text)["extensions"]["cost"]["throttleStatus"][
                        "currentlyAvailable"
                    ]
                    < 100
                ):
                    logger.info("Approaching shopify graphql limit, pausing")
                    time.sleep(10)

            except Exception as e:
                logger.warning("failed to update cover", exc_info=True)

    def cover_image_wrapper(self):
        # redo cover image for all images made today
        all_prods = self.recur_get_products(products_link=None, products=[])
        prods = []
        titles = []
        for prod in all_prods:
            team = prod["title"]
            # on feb 19 I added it so when I update image I add alt text, this can be used to determine which have yet to be updated
            # basically from now on Ill know I need to switch the image If I dont see alt text
            # this is cleaner than it was, but I learned that My printify responses can give me my shopify ID so I could run through a bunch
            # of calls that runs for all of the printify IDs and then gives me a list of the shopify IDs that I could feed here.
            # This might be worse tho, cus this one is more of a catch all like if I cancel a run or something, should just detect stuff that hasnt been through
            if (prod["images"][0]["alt"] is None) and (
                pd.to_datetime(prod["created_at"]).date()
                > pd.to_datetime("2024-02-21").date()
            ):
                # dont forget! stuff that runs on the 20 from workflow wont have alt text and will be published after 19 so itll get picked up.
                # keep updating that date until I get this in main
                # has no alt text = not updated yet
                # published after 02-19
                prods.append(prod)
                titles.append(team)

        self.update_images2(prods, titles)
        logger.info(f"cover image set to back of shirt for {len(prods)} shirts")

    def create_week_collections(self, all_products):
        week_content = {}
        rs = ["regular-season" + " week " + str(x) for x in range(0, 13)]
        ps = ["postseason" + " week " + str(x) for x in range(0, 13)]
        rs.extend(ps)
        for week in rs:
            week_content[week] = []
            for product in all_products:
                if week in product["title"].lower():
                    week_content[week].append(product["id"])

        # this returns a dict of week:[ids for collection]
        return week_content

    def create_team_collections(self, all_products, teams):
        """
        teams should just be a list of every team
        """
        team_content = {}
        logo_content = {}
        "Kansas State Vs Florida Atlantic"

        for product in all_products:
            # my desc has team wrapped in || this prevents kansas for trigger kansas and kansasa state etc
            team1 = product["title"].split(" Vs ")[0]
            team2 = product["title"].split(" Vs ")[1].split(".")[0]

            # team 1 product
            if team1 not in team_content.keys():
                # team collection has not yet been started, add a list with this id under the team
                team_content[team1] = [product["id"]]
            else:
                # team collection has been started, just add this ID to it
                team_content[team1].append(product["id"])

            # team1 logo
            if team1 not in logo_content.keys():
                if team1 in list(teams.name):
                    logo_content[team1] = teams.loc[teams.name == team1].logos.values[0]
                elif team1.upper() in list(teams.abrev):
                    logo_content[team1] = teams.loc[
                        teams.abrev == team1.upper()
                    ].logos.values[0]
                else:
                    logo_content[team1] = self.post_dict["default_logo"]
            # this catches teams that exist and have a 'logo' but its just nan
            if type(logo_content[team1]) == float:
                logo_content[team1] = self.post_dict["default_logo"]

            # team 2 product
            if team2 not in team_content.keys():
                team_content[team2] = [product["id"]]
            else:
                team_content[team2].append(product["id"])

            # team 2 logo
            if team2 not in logo_content.keys():
                if team2 in list(teams.name):
                    logo_content[team2] = teams.loc[teams.name == team2].logos.values[0]
                elif team2.upper() in list(teams.abrev):
                    logo_content[team2] = teams.loc[
                        teams.abrev == team2.upper()
                    ].logos.values[0]
                else:
                    logo_content[team2] = self.post_dict["default_logo"]
            if type(logo_content[team2]) == float:
                logo_content[team2] = self.post_dict["default_logo"]
        # this returns a dict of team:[ids for collection] and a dict of team:logo
        return team_content, logo_content

    def create_round_collections(self, response1):
        """ """
        round_content = {}

        for product in response1.json()["products"]:
            # my desc has team wrapped in || this prevents kansas for trigger kansas and kansasa state etc
            round = product["body_html"].split("ROUND:")[-1]
            if round not in round_content.keys():
                round_content[round] = [product["id"]]
            else:
                round_content[round].append(product["id"])

        # this returns a dict of team:[ids for collection]
        return round_content

    def post_collection(self, id_list, title, link, desc=None, logo=None):
        if desc is None:
            desc = title
        collects = [{"product_id": x} for x in id_list]

        use_logo = False
        if logo is not None:
            logo_rendered = requests.get(logo)
            if logo_rendered.status_code == 200:
                # only use logo if we have link and its valid
                use_logo = True

        if use_logo:
            collection_data = {
                "custom_collection": {
                    "title": title,
                    "image": {"src": logo, "alt": f"{title} Logo"},
                    "collects": collects,
                    "body_html": desc,
                    "sort_order": "created-desc",
                }
            }
        else:
            collection_data = {
                "custom_collection": {
                    "title": title,
                    "collects": collects,
                    "body_html": desc,
                    "sort_order": "created-desc",
                }
            }

        response1 = requests.post(
            link, headers=self.headers_shopify, json=collection_data
        )

        if response1.status_code == 201:
            logger.info(f"collection created {title}")
        else:
            logger.warning(f"could not create collection {title}")
            logger.warning(collects)
            logger.warning(json.loads(response1.text))

    def create_collections_cfb(self, teams):
        products_link = f"https://{self.post_dict[self.version]['shop_name']}.myshopify.com/admin/api/2024-01/products.json"

        all_products = self.recur_get_products(products_link=products_link)


        week_content = self.create_week_collections(all_products)

        team_content, logo_content = self.create_team_collections(all_products, teams)

        collection_link = f"https://{self.post_dict[self.version]['shop_name']}.myshopify.com/admin/api/2023-04/custom_collections.json"
        logger.info("will create collection for each team")
        all_list = []
        for team in team_content.keys():
            id_list = team_content[team]
            if len(id_list) > 0:
                all_list.extend(id_list)
                desc = f"Custom basketball apparel for all the biggest {team} games"
                if team in logo_content.keys():
                    logo = logo_content[team]
                else:
                    logo = None

                time.sleep(0.75)
                self.post_collection(id_list, team, collection_link, desc, logo)

    def recur_get_products(self, products_link=None, products=[]):
        if products_link is None:
            products_link = f"https://{self.post_dict[self.version]['shop_name']}.myshopify.com/admin/api/2024-01/products.json?limit=250"
        response = requests.get(products_link, headers=self.headers_shopify)
        products.extend(response.json()["products"])
        if "next" in response.links.keys():
            # theres another page of products
            call_limit = response.headers["X-Shopify-Shop-Api-Call-Limit"]
            call_split = [int(x) for x in call_limit.split("/")]
            remaining_calls = call_split[1] - call_split[0]
            if remaining_calls == 0:
                time.sleep(10)
            return self.recur_get_products(
                response.links["next"]["url"], products=products
            )
        else:
            return products

    def create_collections_cbb(self, teams, rounds=False):
        all_products = self.recur_get_products(products_link=None, products=[])

        team_content, logo_content = self.create_team_collections(all_products, teams)

        if rounds:
            round_content = self.create_round_collections(all_products)

        collection_link = f"https://{self.post_dict[self.version]['shop_name']}.myshopify.com/admin/api/2023-04/custom_collections.json"
        logger.info("Creating collection for each team")
        all_list = []
        for team in team_content.keys():
            id_list = team_content[team]
            if len(id_list) > 0:
                all_list.extend(id_list)
                desc = f"Custom basketball apparel for all the biggest {team} games"
                if team in logo_content.keys():
                    logo = logo_content[team]
                else:
                    logo = None

                time.sleep(0.75)
                self.post_collection(id_list, team, collection_link, desc, logo)

        if rounds:
            for round in round_content.keys():
                id_list = round_content[round]
                if len(id_list) > 0:
                    time.sleep(0.75)
                    coll_name = str(dt.date.today().year) + " " + round
                    coll_name = coll_name.split("<")[0].replace("|", "")

                    self.post_collection(id_list, coll_name, collection_link)

    def create_collections_rand(self, teams):
        products_link = f"https://{self.post_dict[self.version]['shop_name']}.myshopify.com/admin/api/2024-01/products.json"

        response1 = requests.get(products_link, headers=self.headers_shopify)

        team_content, logo_content = self.create_team_collections(response1, teams)

        collection_link = f"https://{self.post_dict[self.version]['shop_name']}.myshopify.com/admin/api/2023-04/custom_collections.json"

        for team in team_content.keys():
            id_list = team_content[team]
            if len(id_list) > 0:
                time.sleep(0.75)
                self.post_collection(id_list, team, collection_link)

    def delete_collections_recur(self, response, url, exclude):
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Extract and delete each collection
            collections = response.json()["custom_collections"]
            collections = [x for x in collections if x not in exclude]
            if len(collections) > 0:
                logger.info(
                    f"Currently {len(collections)} collections, going to delete all"
                )
                for collection in collections:
                    time.sleep(
                        0.75
                    )  # instead of doing this I should just monitor rate limit
                    collection_id = collection["id"]
                    delete_endpoint = f"https://{self.post_dict[self.version]['shop_name']}.myshopify.com//admin/api/2021-07/custom_collections/{collection_id}.json?limit=250"
                    delete_response = requests.delete(
                        delete_endpoint, headers=self.headers_shopify
                    )

                    # Check if the delete request was successful (status code 200)
                    if delete_response.status_code == 200:
                        pass
                    else:
                        logger.warning(
                            f"Error deleting collection {collection_id}: {delete_response.status_code} - {delete_response.text}"
                        )
                logger.info(
                    "Deleted all those, going to recur again to see if theres more"
                )
                response2 = requests.get(url, headers=self.headers_shopify)
                self.delete_collections_recur(response2, url, exclude)
            else:
                logger.info("No more collections")
                return
        else:
            logger.warning(f"Error: {response.status_code} - {response.text}")

    def delete_collections(self, exclude):
        url = f"https://{self.post_dict[self.version]['shop_name']}.myshopify.com/admin/api/2021-07/custom_collections.json?limit=250"
        # Make the API request to get the list of collections

        response = requests.get(url, headers=self.headers_shopify)
        # this gets collections, and deletes them, until theres no more collections
        self.delete_collections_recur(response, url, exclude)

    def reset_collections(
        self,
        teams=None,
        exclude=[
            "All Products",
            "College Basketball T Shirts",
            "College Basketball Crewnecks",
            "College Football T Shirts",
            "College Football Crewnecks",
        ],
    ):
        self.delete_collections(exclude)
        if self.version == "cfb":
            self.create_collections_cfb(teams)
        elif self.version == "rand":
            self.create_collections_rand(teams)
        elif self.version == "cbb":
            self.create_collections_cbb(teams)

    def set_prices(self, t_price, s_price):
        logger.info(
            f"about to set every t shirt in the store to ${t_price} and every sweater to ${s_price}"
        )
        products = self.recur_get_products(products_link=None, products=[])

        for product in products:
            if product["product_type"] == "T-Shirt":
                logger.info(
                    f'Updating {product["title"]}, {product["product_type"]} to {t_price}'
                )
                # Update each variant's price
                for variant in product["variants"]:
                    if int(float(variant["price"])) == int(t_price):
                        logger.info("price already there")
                    else:
                        variant_id = variant["id"]
                        update_url = f"https://{self.post_dict[self.version]['shop_name']}.myshopify.com/admin/api/2024-01/variants/{variant_id}.json"
                        update_data = {"variant": {"id": variant_id, "price": t_price}}
                        resp = requests.put(
                            update_url, json=update_data, headers=self.headers_shopify
                        )
                        if resp.status_code == 200:
                            time.sleep(0.5)  # should just monitor rate limit
                        else:
                            logger.warning("fail")
                            logger.warning(resp.status_code)
                            logger.warning(resp.text)
                logger.info("success")
            # need to actually find out what this product type is this is a guess
            elif product["product_type"] == "Sweatshirt":
                logger.info(
                    f'Updating {product["title"]}, {product["product_type"]} to {s_price}'
                )
                # Update each variant's price
                for variant in product["variants"]:
                    if int(float(variant["price"])) == int(s_price):
                        logger.info("price already there")
                    else:
                        variant_id = variant["id"]
                        update_url = f"https://{self.post_dict[self.version]['shop_name']}.myshopify.com/admin/api/2024-01/variants/{variant_id}.json"
                        update_data = {"variant": {"id": variant_id, "price": s_price}}
                        resp = requests.put(
                            update_url, json=update_data, headers=self.headers_shopify
                        )
                        if resp.status_code == 200:
                            time.sleep(0.5)  # should just monitor rate limit
                        else:
                            logger.warning("fail")
                            logger.warning(resp.status_code)
                            logger.warning(resp.text)
                logger.info("success")
