import requests
import base64
from io import BytesIO
import json
import time

class shopify_printify():
    def __init__(self,post_dict):
        self.post_dict = post_dict
        self.headers_printify = {
        "Authorization": f"Bearer {post_dict['printify_access']}",
        "Content-Type": "application/json",
        }
        self.headers_shopify = {
            "X-Shopify-Access-Token": post_dict["shopify_access"],
            "Content-Type": "application/json",
        }

    def post(self, publish=False):
        upload_url = f"{self.post_dict['base_url']}/uploads/images.json"
        product_url = f"{self.post_dict['base_url']}/shops/{self.post_dict['shop_id']}/products.json"

        # this posts a design, but doesnt publish it
        buffered = BytesIO()
        self.post_dict["design"].save(buffered, format="png")
        img = base64.b64encode(buffered.getvalue()).decode("utf-8")

        # Upload the image to the Printify media library
        data = {"file_name": self.post_dict["title"], "contents": img}
        img_response = requests.post(upload_url, headers=self.headers_printify, json=data)

        buffered = BytesIO()
        self.post_dict["text"].save(buffered, format="png")
        txt = base64.b64encode(buffered.getvalue()).decode("utf-8")

        data = {"file_name": self.post_dict["title"] + "txt", "contents": txt}
        txt_response = requests.post(upload_url, headers=self.headers_printify, json=data)

        if img_response.status_code == 200 and txt_response.status_code == 200:
            print("image and text sent to printify")
            image_id = img_response.json()["id"]
            text_id = txt_response.json()["id"]
            variants = [
                {"id": id, "price": self.post_dict["price"], "is_enabled": True}
                for id in self.post_dict["variant_ids"]
            ]
            # this might not work because I dont think Ill have the idea until after I post it
            data = {
                "title": self.post_dict["title"],
                "description": self.post_dict["description"],
                "tags": self.post_dict["tags"].split(
                    ", "
                ),  # Assuming tags are comma-separated in the CSV
                "blueprint_id": self.post_dict["blueprint_id"],
                "print_provider_id": self.post_dict["print_provider_id"],
                "variants": variants,
                "print_areas": [
                    {
                        "variant_ids": self.post_dict[
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

                                        "id": text_id,
                                        "x": 0.25,
                                        "y": 0.25,
                                        "scale": 0.3,
                                        "angle": 0,
                                    }
                                ],
                            },
                        ],
                    }
                ],
            }

            response1 = requests.post(product_url, headers=self.headers_printify, json=data)
            if response1.status_code == 200:
                print("Product posted successfully in Printify")
            else:
                print("Failed to post product in Printify")

            if publish:
                # this part does the publishing
                printify_publish = f"{self.post_dict['base_url']}/shops/{self.post_dict['shop_id']}/products/{json.loads(response1.text)['id']}/publish.json"

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
                    printify_publish, headers=self.headers_printify, json=update_data
                )
                if response2.status_code == 200:
                    print("Product published successfully in Printify")
                else:
                    print("Failed to publish product in Printify")
        else:
            print("unable to send image to printify")


    def image_module(item):
        url_title = item["title"].replace(" ","-").replace(",","").replace(".","").lower()

        variant = 12100
        b1a = f'https://images-api.printify.com/mockup/{item["id"]}/{variant}/92571/{url_title}.jpg?camera_label=back'
        b2a = f'https://images-api.printify.com/mockup/{item["id"]}/{variant}/92570/{url_title}.jpg?camera_label=front'
        b3a = f'https://images-api.printify.com/mockup/{item["id"]}/{variant}/92572/{url_title}.jpg?camera_label=person-1'

        variant = 12070 # other color
        b1b = f'https://images-api.printify.com/mockup/{item["id"]}/{variant}/92571/{url_title}.jpg?camera_label=back'
        b2b = f'https://images-api.printify.com/mockup/{item["id"]}/{variant}/92570/{url_title}.jpg?camera_label=front'
        b3b = f'https://images-api.printify.com/mockup/{item["id"]}/{variant}/92572/{url_title}.jpg?camera_label=person-1'



        new_base = [
        {'src': f'{b1a}',
        'variant_ids': [12100, 12101, 12102, 12103, 12104],
        'position': 'back',
        'is_default': True,
        'is_selected_for_publishing': True},
        {'src': f'{b2a}',
        'variant_ids': [12100, 12101, 12102, 12103, 12104],
        'position': 'front',
        'is_default': False,
        'is_selected_for_publishing': True},
        {'src': f'{b3a}',
        'variant_ids': [12100, 12101, 12102, 12103, 12104],
        'position': 'other',
        'is_default': False,
        'is_selected_for_publishing': True},

        {'src': f'{b1b}',
        'variant_ids': [12070, 12071, 12072, 12073, 12074],
        'position': 'back',
        'is_default': True,
        'is_selected_for_publishing': True},
        {'src': f'{b2b}',
        'variant_ids': [12070, 12071, 12072, 12073, 12074],
        'position': 'front',
        'is_default': False,
        'is_selected_for_publishing': True},
        {'src': f'{b3b}',
        'variant_ids': [12070, 12071, 12072, 12073, 12074],
        'position': 'other',
        'is_default': False,
        'is_selected_for_publishing': True}
        ]
        return new_base

    def update_images(self,to_do):
        """
        to do is a list of title of shirt I want to change images for

        This aint working but I feel like it should
        
        Following api reference from the update product thing here
        https://developers.printify.com/#products

        Could probably post and then update a bunch of images on shopify, but thats aggressive
        https://shopify.dev/docs/api/admin-rest/2023-10/resources/product-image#post-products-product-id-images
        """

        # get products
        product_url = f"{self.post_dict['base_url']}/shops/{self.post_dict['shop_id']}/products.json"
        response = requests.get(product_url, self.headers_printify)

        for item in response['data']:
            if item['title'] in [to_do]:
                new_images = self.image_module(item)

                url2 = f'https://api.printify.com/v1/shops/{self.post_dict["shop_id"]}/products/{item["id"]}.json'

                resp = requests.put(url2, headers = self.headers_printify, data = new_images)


        

    def create_week_collections(self,response1):

        week_content={}
        rs = ['regular-season'+' Week '+str(x) for x in range(0,13)]
        ps = ['postseason'+' Week '+str(x) for x in range(0,13)]
        rs.extend(ps)
        for week in rs:
            week_content[week] = []
            for product in response1.json()["products"]:
                if week in product["title"]:
                    week_content[week].append(product["id"])

        # this returns a dict of week:[ids for collection]
        return week_content
        
    def create_team_collections(self,response1,teams):
        '''
        teams should just be a list of every team
        '''
        team_content={}
        
        for team in teams:
            team_content[team] = []
            for product in response1.json()["products"]:
                # my desc has team wrapped in || this prevents kansas for trigger kansas and kansasa state etc
                if '||'+team+'||' in product["body_html"]:
                    team_content[team].append(product["id"])

        # this returns a dict of team:[ids for collection]
        return team_content
    def post_collection(self,id_list,title,link):
            collects = [{"product_id": x} for x in id_list]
            collection_data = {
                "custom_collection": {
                    "title": title,
                    "collects": collects,
                }
            }
            response1 = requests.post(
                link, headers=self.headers_shopify, json=collection_data
            )
            if response1.status_code == 201:
                print(f"collection created {title}")
            else:
                print("could not create collection")
                print(json.loads(response1.text))
    
    def create_collections(self,teams):
        products_link = f"https://{self.post_dict['shop_name']}.myshopify.com/admin/api/2024-01/products.json"

        response1 = requests.get(products_link, headers=self.headers_shopify)

        week_content = self.create_week_collections(response1)

        team_content = self.create_team_collections(response1,teams)

        collection_link = f"https://{self.post_dict['shop_name']}.myshopify.com/admin/api/2023-04/custom_collections.json"

        for week in week_content.keys():
            id_list = week_content[week]
            if len(id_list)>0:
                time.sleep(0.75)
                self.post_collection(id_list,week,collection_link)

        for team in team_content.keys():
            id_list = team_content[team]
            if len(id_list)>0:
                time.sleep(0.75)
                self.post_collection(id_list,team,collection_link)

        

    def delete_collections(self):
        url = f"https://{self.post_dict['shop_name']}.myshopify.com/admin/api/2021-07/custom_collections.json"
        # Make the API request to get the list of collections
        response = requests.get(url, headers = self.headers_shopify)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Extract and delete each collection
            collections = response.json()["custom_collections"]
            for collection in collections:
                time.sleep(1)
                collection_id = collection["id"]
                delete_endpoint = f"https://{self.post_dict['shop_name']}.myshopify.com//admin/api/2021-07/custom_collections/{collection_id}.json"
                delete_response = requests.delete(delete_endpoint, headers=self.headers_shopify)

                # Check if the delete request was successful (status code 200)
                if delete_response.status_code == 200:
                    print(f"Collection with ID {collection_id} deleted successfully.")
                else:
                    print(f"Error deleting collection {collection_id}: {delete_response.status_code} - {delete_response.text}")
        else:
            print(f"Error: {response.status_code} - {response.text}")

    def reset_collections(self,teams):
        self.delete_collections()
        self.create_collections(teams)

