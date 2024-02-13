import json
import requests
from PIL import Image
from openai import OpenAI
import random


def dalle_image(client, prompt, v):
    response = client.images.generate(
        model=f"dall-e-{v}",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url

    image = Image.open(requests.get(image_url, stream=True).raw)
    return image


def generate_main(prompt, dalle_key, test=True, dalle=3, retry=True):
    if test:
        print("using saved image because test mode")
        main_image = Image.open(r"test3.png")
    else:
        client = OpenAI(api_key=dalle_key)

        try:
            main_image = dalle_image(client, prompt, v=dalle)
        except Exception as e:
            print(prompt)
            print("failed to generate image")
            if retry:
                generate_main(prompt, dalle_key, test, dalle, retry=False)
            print("Retry failed too, will return none")
            print(e)
            return None

    return main_image


def prompt_engineer(sport, team1, team2, mascot1=None, mascot2=None):
    """ """
    if mascot1 is None:
        mascot1 = ""
    if mascot2 is None:
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
    print(f"Prompt: {prompt}")
    no_detail = f"I NEED to test how the tool works with extremely simple prompts. DO NOT add any detail, just use it AS-IS:{prompt}. Remember to use exactly this prompt. If you change even a single word or character, I’ll fire you!"
    return no_detail
