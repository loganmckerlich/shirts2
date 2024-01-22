import json
import requests
from PIL import Image
from openai import OpenAI

def dalle_image(client,prompt):
    response = client.images.generate(
    model="dall-e-3",
    prompt=prompt,
    size="1024x1024",
    quality="standard",
    n=1,
    )

    image_url = response.data[0].url

    image = Image.open(requests.get(image_url, stream=True).raw)
    return image

def generate_main(prompt, dalle_key, test=True):
    if test:
        print("using saved image because test mode")
        main_image = Image.open(r"test3.png")
    else:
        client = OpenAI(api_key=dalle_key)

        try:
            main_image = dalle_image(client,prompt)
        except Exception as e:
            print(prompt)
            print('failed to generate image, will skip')
            print(e)
            return None


    return main_image
