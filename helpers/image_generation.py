import json
import requests
from datetime import datetime as dt
from PIL import Image


def generate_main(game_id,sfx,prompt,sdapi,test=True):
    if test:
        print('using saved image because test mode')
        main_image = Image.open(r'test3.png')
    else:
        print('generating image')
        url = "https://stablediffusionapi.com/api/v3/text2img"
        payload = json.dumps({
        "key": sdapi,
        "prompt": prompt,
        "negative_prompt": None,
        "width": "512",
        "height": "512",
        "samples": "1",
        "num_inference_steps": "20",
        "seed": None,
        "guidance_scale": 7.5,
        "safety_checker": "yes",
        "multi_lingual": "no",
        "panorama": "no",
        "self_attention": "no",
        "upscale": "no",
        "embeddings_model": None,
        "webhook": None,
        "track_id": None
        })

        headers = {
        'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, data=payload)
        print(response.status_code)
        print(json.loads(response.text))
        # output[0] is a png
        img = json.loads(response.text)["output"][0]
        main_image = Image.open(requests.get(img, stream=True).raw)

    return main_image