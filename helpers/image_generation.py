import json
import requests
from datetime import datetime as dt
from PIL import Image


def generate_main(prompt,sdapi,test=True):
    if test:
        print('using saved image')
        main_image = Image.open(r'prompt.png')
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

        response = requests.request("POST", url, headers=headers, data=payload)

        # output[0] is a png
        img = json.loads(response.text)["output"][0]
        main_image = Image.open(requests.get(img, stream=True).raw)
        main_image.save(f"{prompt}_{str(dt.now()).replace(' ','_')}.png","PNG")
    return main_image