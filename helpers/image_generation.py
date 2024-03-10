import json
import requests
from PIL import Image
from openai import OpenAI
import random
import math
import logging

logger = logging.getLogger()


def dalle_image(client, prompt, v, retry):
    fail = False
    try:
        response = client.images.generate(
            model=f"dall-e-{v}",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
    except:
        if retry:
            logger.info('Retrying')
            try:
                response = client.images.generate(
                model=f"dall-e-{v}",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
                )
            except:
                fail = True
        else:
            fail = True
    
    if fail:
        return 'filtered'


    image_url = response.data[0].url
    
    inter = requests.get(image_url, stream=True)

    image = Image.open(inter.raw)

    return image


def generate_main(prompt, dalle_key, test=True, dalle=3, retry=True):
    if test:
        logger.info("using saved image because test mode")
        main_image = Image.open(r"test3.png")
    else:
        client = OpenAI(api_key=dalle_key)

        main_image = dalle_image(client, prompt, v=dalle, retry= retry)

        if main_image == 'filtered':
            logger.warning("image generation didnt work (likely content filter)")
            return None

        return main_image


def prompt_engineer(sport, team1, team2, mascot1=None, mascot2=None):
    # type checking because sometimes its nan sometimes its None
    if type(mascot1) != str:
        mascot1 = ""
    if type(mascot2) != str:
        mascot2 = ""

    styles = [
        "Street Fighter",
        "Pokemon battle",
        "Family guy",
        "Simpsons",
        "Starwars Jedi vs Sith",
        "Mickey Mouse Disney",
        "pixel art",
        "cutout",
        "claymation Wallace and Grommet",
        "Dragon Ball Z Goku vs Saitama",
        "Minecraft",
        "Samurai Battle",
        "Renaissance Painting",
        "Charcoal Sketch",
        "Oil Painting",
    ]

    mystyle = random.choice(styles)
    prompt = f"""
        Generate an image of the {team1} {mascot1} mascot fighting the {team2} {mascot2} mascot.
        It is a fierce battle centered around {sport}. Depict the battle in a {mystyle} animation style.
        """
    logger.info(f"Prompt: {prompt}")
    no_detail = f"I NEED to test how the tool works with extremely simple prompts. DO NOT add any detail, just use it AS-IS:{prompt}. Remember to use exactly this prompt. If you change even a single word or character, I’ll fire you!"
    return no_detail
