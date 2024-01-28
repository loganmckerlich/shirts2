from PIL import Image, ImageOps, ImageDraw, ImageFont
from .image_generation import generate_main, prompt_engineer
import requests
import pandas as pd
import numpy as np
from unidecode import unidecode


def size_font_recur(img_draw, team1, team2, W, font, size):
    mainfont = ImageFont.truetype(
        rf"./fonts/{font}.ttf", size=size, layout_engine=ImageFont.Layout.BASIC
    )

    _, _, r1, _ = img_draw.textbbox((0, 0), team1, font=mainfont)

    _, _, rv, _ = img_draw.textbbox((0, 0), "VS", font=mainfont)

    _, _, r2, _ = img_draw.textbbox((0, 0), team2, font=mainfont)

    if (r1 + rv + r2) <= W:
        return mainfont
    else:
        size -= 1
        return size_font_recur(img_draw, team1, team2, W, font, size)


def simple_size_font_recur(img_draw, text, W, font, size):
    mainfont = ImageFont.truetype(
        rf"./fonts/{font}.ttf", size=size, layout_engine=ImageFont.Layout.BASIC
    )

    _, _, r, _ = img_draw.textbbox((0, 0), text, font=mainfont)

    if r <= W:
        return mainfont
    else:
        size -= 1
        return simple_size_font_recur(img_draw, text, W, font, size)


def ar_resize(new,image):
    # it will be new tall
    current = image.size
    ar = current[0]/current[1]
    image=image.resize((int(np.floor(new*ar)),new))
    return image
    

def build_cbb(config, test=True):
    # total size

    W, H = config["W"], config["H"]

    # main image size

    iw, ih = config["iw"], config["ih"]

    # logo size

    lw, lh = config["lw"], config["lh"]

    team1 = config["team1"]["name"]

    team1color = config["team1"]["color"]

    team2 = config["team2"]["name"]

    team2color = config["team2"]["color"]

    sport = 'basketball'

    prompt = prompt_engineer(sport,team1,team2,mascot1 = config["team1"]["mascot"], mascot2=config["team2"]["mascot"])

    gamedate = config["date"]

    logo_buffer = config["logo_buffer"]

    if test:
        bg = Image.new("RGBA", (W, H), color="white")
    else:
        bg = Image.new("RGBA", (W, H))

    main_image = generate_main(
        prompt, config["dalle_key"], test=test, dalle = config['dalle']
    )
    if main_image is not None:
        main_image = main_image.resize((iw, ih))


        if main_image == None:
            print('image failed to generate')
            print(prompt)
            return None,None

        try:
            logo1 = Image.open(
                requests.get(config["team1"]["logo"], stream=True).raw
            )
        except:
            logo1 = Image.open(
                requests.get(config["default_logo"], stream=True).raw
            )

        try:
            logo2 = Image.open(
                requests.get(config["team2"]["logo"], stream=True).raw
            )
        except:
            logo2 = Image.open(
                requests.get(config["default_logo"], stream=True).raw
            )

        logo1 = ar_resize(lh,logo1)
        logo2 = ar_resize(lh,logo2)

        img_w, img_h = main_image.size

        # Paste with Coordinates

        offset = ((W - iw) // 2, 0)

        bg.paste(main_image, offset)

        bg.alpha_composite(logo1, (0 + logo_buffer, ih))

        bg.alpha_composite(logo2, (W - logo_buffer - lw, ih))

        img_draw = ImageDraw.Draw(bg)

        mainfont = size_font_recur(img_draw, team1, team2, W, "Freshman", size=150)

        score_font = ImageFont.truetype(
            r"./fonts/Freshman.ttf", size=70, layout_engine=ImageFont.Layout.BASIC
        )

        date_font = ImageFont.truetype(
            r"./fonts/Freshman.ttf", size=22, layout_engine=ImageFont.Layout.BASIC
        )

        desc_font = simple_size_font_recur(img_draw, config['desc'], W, 'Universal_Serif', 150)

        l1, t1, r1, b1 = img_draw.textbbox((0, img_h), team1, font=mainfont)

        lv, tv, rv, bv = img_draw.textbbox((r1 + 5, img_h), "VS", font=mainfont)

        l2, t2, r2, b2 = img_draw.textbbox((rv + 5, img_h), team2, font=mainfont)

        _, _, wd, hd = img_draw.textbbox((0, 0), gamedate, font=date_font)

        _, _, w1, h1 = img_draw.textbbox((0, 0), str(config["team1"]["score"]), font=score_font)

        _, _, w2, h2 = img_draw.textbbox((0, 0), str(config["team2"]["score"]), font=score_font)


        img_draw.text(
            (l1, t1 + lh + 5),
            team1,
            team1color,
            font=mainfont,
            stroke_width=1,
            stroke_fill="black",
        )

        img_draw.text(
            (lv, tv + lh + 5),
            "VS",
            (255, 255, 255),
            font=mainfont,
            stroke_width=1,
            stroke_fill="black",
        )

        img_draw.text(
            (l2, t2 + lh + 5),
            team2,
            team2color,
            font=mainfont,
            stroke_width=1,
            stroke_fill="black",
        )

        img_draw.text(
            ((W - wd) / 2, ih + (logo2.size[1] // 2) - (hd // 2)),
            gamedate,
            (255, 255, 255),
            font=date_font,
            stroke_width=1,
            stroke_fill="black",
        )

        if config["team1"]["score"] is not None:
            img_draw.text(
                ((W // 4), bv + h1),
                str(config["team1"]["score"]),
                team1color,
                font=score_font,
                stroke_width=1,
                stroke_fill="black",
            )

            img_draw.text(
                (((W // 4) * 3 - w2), bv + h2),
                str(config["team2"]["score"]),
                team2color,
                font=score_font,
                stroke_width=1,
                stroke_fill="black",
            )

            img_draw.text(
                (l1,(bv + h2+ h1)),
                config['desc'],
                font=desc_font,
                fill="black"
            )
        else:
            img_draw.text(
                (l1,(bv + h2)),
                config['desc'],
                font=desc_font,
                fill="black"
            )

        text = Image.new("RGBA", (W, H))

        text_draw = ImageDraw.Draw(text)

        if config["team1"]["mascot"]is not None and  config["team2"]["mascot"] is not None:
            game_text = f"{team1} {config['team1']['mascot']} Vs. {team2} {config['team2']['mascot']}\n{gamedate}"
        else:
            game_text = f"{team1} Vs. {team2}\n{gamedate}"

        game_font = simple_size_font_recur(text_draw, game_text, W, "Universal_Serif", 75)

        text_draw.text((0, 0), game_text, font=game_font, fill="black")

        return bg, text
    else:
        return 'prompt failed'

def build_cfb(config, test=False):
    # total size

    W, H = config["W"], config["H"]

    # main image size

    iw, ih = config["iw"], config["ih"]

    # logo size

    lw, lh = config["lw"], config["lh"]

    team1 = config["home_team"]["shortn"]

    team1full = config["home_team"]["longn"]

    team1color = config["home_team"]["color"]

    team2 = config["away_team"]["shortn"]

    team2full = config["away_team"]["longn"]

    team2color = config["away_team"]["color"]

    sport = config["sport"]

    score = config["game"]["score"]

    game_date = config["game"]["date"]

    prompt = prompt_engineer(sport,team1full,team2full,mascot1 = config["home_team"]["mascot"], mascot2=config["away_team"]["mascot"])

    gamedate = config["game"]["date"]

    logo_buffer = config["logo_buffer"]

    if test:
        bg = Image.new("RGBA", (W, H), color="white")
    else:
        bg = Image.new("RGBA", (W, H))

    main_image = generate_main(
        prompt, config["dalle_key"], test=test, dalle = config['dalle']
    )
    if main_image is not None:
        main_image = main_image.resize((iw, ih))

        try:
            logo1 = Image.open(
                requests.get(config["home_team"]["logo"], stream=True).raw
            ).resize((lw, lh))
        except:
            logo1 = Image.open(
                requests.get(config["default_logo"], stream=True).raw
            ).resize((lw, lh))

        try:
            logo2 = Image.open(
                requests.get(config["away_team"]["logo"], stream=True).raw
            ).resize((lw, lh))
        except:
            logo2 = Image.open(
                requests.get(config["default_logo"], stream=True).raw
            ).resize((lw, lh))

        img_w, img_h = main_image.size

        # Paste with Coordinates

        offset = ((W - iw) // 2, 0)

        bg.paste(main_image, offset)

        bg.alpha_composite(logo1, (0 + logo_buffer, ih))

        bg.alpha_composite(logo2, (W - logo_buffer - lw, ih))

        img_draw = ImageDraw.Draw(bg)

        mainfont = size_font_recur(img_draw, team1, team2, W, "Freshman", size=150)

        score_font = ImageFont.truetype(
            r"./fonts/Freshman.ttf", size=70, layout_engine=ImageFont.Layout.BASIC
        )

        date_font = ImageFont.truetype(
            r"./fonts/alarm_clock.ttf", size=22, layout_engine=ImageFont.Layout.BASIC
        )  # autosize this

        l1, t1, r1, b1 = img_draw.textbbox((0, img_h), team1, font=mainfont)

        lv, tv, rv, bv = img_draw.textbbox((r1 + 5, img_h), "VS", font=mainfont)

        l2, t2, r2, b2 = img_draw.textbbox((rv + 5, img_h), team2, font=mainfont)

        _, _, wd, hd = img_draw.textbbox((0, 0), gamedate, font=date_font)

        _, _, w1, h1 = img_draw.textbbox((0, 0), str(score[0]), font=score_font)

        _, _, w2, h2 = img_draw.textbbox((0, 0), str(score[1]), font=score_font)

        img_draw.text(
            (l1, t1 + lh + 5),
            team1,
            team1color,
            font=mainfont,
            stroke_width=1,
            stroke_fill="black",
        )

        img_draw.text(
            (lv, tv + lh + 5),
            "VS",
            (255, 255, 255),
            font=mainfont,
            stroke_width=1,
            stroke_fill="black",
        )

        img_draw.text(
            (l2, t2 + lh + 5),
            team2,
            team2color,
            font=mainfont,
            stroke_width=1,
            stroke_fill="black",
        )

        img_draw.text(
            ((W - wd) / 2, ih + (logo2.size[1] // 2) - (hd // 2)),
            gamedate,
            (255, 255, 255),
            font=date_font,
            stroke_width=1,
            stroke_fill="black",
        )

        if config["game"]["done"]:
            img_draw.text(
                ((W // 4), bv + h1),
                str(score[0]),
                team1color,
                font=score_font,
                stroke_width=1,
                stroke_fill="black",
            )

            img_draw.text(
                (((W // 4) * 3 - w2), bv + h2),
                str(score[1]),
                team2color,
                font=score_font,
                stroke_width=1,
                stroke_fill="black",
            )

        text = Image.new("RGBA", (W, H))

        text_draw = ImageDraw.Draw(text)

        game_text = f"{team1} Vs. {team2}\n{game_date}"

        game_font = simple_size_font_recur(text_draw, game_text, W, "Universal_Serif", 75)

        text_draw.text((0, 0), game_text, font=game_font, fill="black")

        return bg, text
    else:
        return 'Prompt Failed'

def no_caption_image(design_config,main_image):
    bg = Image.new("RGBA", (design_config['W'], design_config['H']))

    main_image=main_image.resize((design_config['W'], design_config['W']))
    bg.paste(main_image)

    return bg

def simple_text(design_config,text_in):
    text = Image.new("RGBA", (design_config['W'], design_config['H']))

    text_draw = ImageDraw.Draw(text)

    game_font = simple_size_font_recur(text_draw, text_in, design_config['W'], "Universal_Serif", 75)

    text_draw.text((0, 0), text_in, font=game_font, fill="black")

    return text