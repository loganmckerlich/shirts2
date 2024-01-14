import requests
import base64
from io import BytesIO
import json


def post(post_dict, publish=False):
    upload_url = f"{post_dict['base_url']}/uploads/images.json"
    product_url = f"{post_dict['base_url']}/shops/{post_dict['shop_id']}/products.json"

    headers = {
        "Authorization": f"Bearer {post_dict['printify_access']}",
        "Content-Type": "application/json",
    }

    # this posts a design, but doesnt publish it
    buffered = BytesIO()
    post_dict["design"].save(buffered, format="png")
    img = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # Upload the image to the Printify media library
    data = {"file_name": post_dict["title"], "contents": img}
    img_response = requests.post(upload_url, headers=headers, json=data)

    buffered = BytesIO()
    post_dict["text"].save(buffered, format="png")
    txt = base64.b64encode(buffered.getvalue()).decode("utf-8")

    data = {"file_name": post_dict["title"] + "txt", "contents": txt}
    txt_response = requests.post(upload_url, headers=headers, json=data)

    if img_response.status_code == 200 and txt_response.status_code == 200:
        print("image and text sent to printify")
        image_id = img_response.json()["id"]
        text_id = txt_response.json()["id"]
        variants = [
            {"id": id, "price": post_dict["price"], "is_enabled": True}
            for id in post_dict["variant_ids"]
        ]

        data = {
            "title": post_dict["title"],
            "description": post_dict["description"],
            "tags": post_dict["tags"].split(
                ", "
            ),  # Assuming tags are comma-separated in the CSV
            "blueprint_id": post_dict["blueprint_id"],
            "print_provider_id": post_dict["print_provider_id"],
            "variants": variants,
            "print_areas": [
                {
                    "variant_ids": post_dict[
                        "variant_ids"
                    ],  # Replace with the actual variant ID
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
                                    # 'id': text_id,
                                    # 'x': 0,
                                    # 'y': 0,
                                    # 'scale': 0.25,
                                    # 'angle': 0
                                    "id": text_id,
                                    "x": 0.5,
                                    "y": 0.5,
                                    "scale": 0.75,
                                    "angle": 0,
                                }
                            ],
                        },
                    ],
                }
            ],
        }

        response1 = requests.post(product_url, headers=headers, json=data)
        if response1.status_code == 200:
            print("Product posted successfully in Printify")
        else:
            print("Failed to post product in Printify")

        if publish:
            # this part does the publishing
            printify_publish = f"{post_dict['base_url']}/shops/{post_dict['shop_id']}/products/{json.loads(response1.text)['id']}/publish.json"

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
                printify_publish, headers=headers, json=update_data
            )
            if response2.status_code == 200:
                print("Product published successfully in Printify")
            else:
                print("Failed to publish product in Printify")
    else:
        print("unable to send image to printify")


def get_items(created, post_dict):
    """
    get items, so we can filter by name to get shopify id to add to collection
    created is a list of all the things we just made to add to the list
    """
    shopify_headers = {
        "X-Shopify-Access-Token": post_dict["shopify_access"],
        "Content-Type": "application/json",
    }
    products_link = f"https://{post_dict['shop_name']}.myshopify.com/admin/api/2024-01/products.json"

    response1 = requests.get(products_link, headers=shopify_headers)
    print("got all items")
    id_list = []
    print(created)
    for product in response1.json()["products"]:
        if product["title"] in created:
            id_list.append(product["id"])
            print(f'    adding {product["title"]} to the collection')
    print("filtered list for just this collection")
    return id_list


def create_collection(created, week, year, post_dict, pref):
    """
    created is a list of titles, not ids

    give this a list of product names (created) and it will add them to a collection for the week

    add something for the whole has the game happened yet aspect
    """
    if pref == "pre":
        label = "Anticipation Of Games"
    elif pref == "post":
        label = "Reaction To Games"
    else:
        print("unavail pref")
    shopify_headers = {
        "X-Shopify-Access-Token": post_dict["shopify_access"],
        "Content-Type": "application/json",
    }
    collection_link = f"https://{post_dict['shop_name']}.myshopify.com/admin/api/2023-04/custom_collections.json"

    id_list = get_items(created, post_dict)
    collects = [{"product_id": x} for x in id_list]
    collection_data = {
        "custom_collection": {
            "title": f"{label}: Week {week}, {year}",
            "collects": collects,
        }
    }
    response1 = requests.post(
        collection_link, headers=shopify_headers, json=collection_data
    )
    if response1.status_code == 201:
        print("collection created")
    else:
        print("could not create collection")
        print(json.loads(response1.text))
