from PIL import Image, ImageOps, ImageDraw, ImageFont
from .image_generation import generate_main, prompt_engineer
import requests
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger()


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


def ar_resize(new, image):
    # it will be new tall
    current = image.size
    ar = current[0] / current[1]
    image = image.resize((int(np.floor(new * ar)), new))
    return image


def type_check_score(score):
    # check if score is none or nan or float
    if score is None:
        return None
    elif (type(score) == float) or (type(score) == np.float64):
        if str(score) == "nan":
            return None
        else:
            return int(score)
    elif "." in str(score):
        return int(score)
    else:
        return score


def build_cbb(config, test=True):
    # total size

    W, H = config["W"], config["H"]

    # main image size

    iw, ih = config["iw"], config["ih"]

    # logo size

    lw, lh = config["lw"], config["lh"]

    team1 = config["team1"]["name"]

    rank1 = config["team1"]["rank"]

    team1color = config["team1"]["color"]

    team2 = config["team2"]["name"]

    rank2 = config["team2"]["rank"]

    if rank1 is not None:
        team1r = " #" + rank1[1:-1] + " " + team1
    else:
        team1r = " " + team1

    if rank2 is not None:
        team2r = "#" + rank2[1:-1] + " " + team2 + " "
    else:
        team2r = team2 + " "

    team2color = config["team2"]["color"]

    sport = "basketball"

    prompt = prompt_engineer(
        sport,
        team1,
        team2,
        mascot1=config["team1"]["mascot"],
        mascot2=config["team2"]["mascot"],
    )

    gamedate = config["date"]

    logo_buffer = config["logo_buffer"]

    if test:
        bg = Image.new("RGBA", (W, H), color="white")
    else:
        bg = Image.new("RGBA", (W, H))

    main_image = generate_main(
        prompt, config["dalle_key"], test=test, dalle=config["dalle"]
    )
    if main_image is not None:
        main_image = main_image.resize((iw, ih))

        if main_image == None:
            logger.warning("image failed to generate")
            logger.info(prompt)
            return None, None

        try:
            logo1 = Image.open(requests.get(config["team1"]["logo"], stream=True).raw)
        except:
            logo1 = Image.open(requests.get(config["default_logo"], stream=True).raw)

        try:
            logo2 = Image.open(requests.get(config["team2"]["logo"], stream=True).raw)
        except:
            logo2 = Image.open(requests.get(config["default_logo"], stream=True).raw)

        logo1 = ar_resize(lh, logo1)
        logo2 = ar_resize(lh, logo2)

        img_w, img_h = main_image.size

        # Paste with Coordinates

        offset = ((W - iw) // 2, 0)

        bg.paste(main_image, offset)
        try:
            # transparent background
            bg.alpha_composite(logo1, (0 + logo_buffer, ih))
        except:
            try:
                # not transparent
                bg.paste(logo1, (0 + logo_buffer, ih))
                logger.warning(f"{team1} failed transparent worked normal")
            except:
                logger.warning(f"{team1} fail loggo")

        try:
            bg.alpha_composite(logo2, (W - logo_buffer - lw, ih))
        except:
            try:
                # not transparent
                bg.paste(logo2, (W - logo_buffer - lw, ih))
                logger.warning(f"{team2} failed transparent worked normal")
            except:
                logger.warning(f"{team2} fail  logo")

        img_draw = ImageDraw.Draw(bg)

        mainfont = size_font_recur(img_draw, team1r, team2r, W, "Freshman", size=150)

        score_font = ImageFont.truetype(
            r"./fonts/Freshman.ttf", size=70, layout_engine=ImageFont.Layout.BASIC
        )

        date_font = ImageFont.truetype(
            r"./fonts/Freshman.ttf", size=22, layout_engine=ImageFont.Layout.BASIC
        )
        try:
            desc_font = simple_size_font_recur(
                img_draw, config["desc"], W, "Universal_Serif", 150
            )
            no_desc = False
        except:
            no_desc = True
        l1, t1, r1, b1 = img_draw.textbbox((0, img_h), team1r, font=mainfont)

        lv, tv, rv, bv = img_draw.textbbox((r1 + 5, img_h), "VS", font=mainfont)

        l2, t2, r2, b2 = img_draw.textbbox((rv + 5, img_h), team2r, font=mainfont)

        _, _, wd, hd = img_draw.textbbox((0, 0), gamedate, font=date_font)

        # sometimes even when I should have the score, I get a float or a nan. fix
        team1_score = type_check_score(config["team1"]["score"])
        team2_score = type_check_score(config["team2"]["score"])

        _, _, w1, h1 = img_draw.textbbox((0, 0), str(team1_score), font=score_font)

        _, _, w2, h2 = img_draw.textbbox((0, 0), str(team2_score), font=score_font)

        img_draw.text(
            (l1, t1 + lh + 5),
            team1r,
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
            team2r,
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

        if (team1_score is not None) and (team2_score is not None):
            if (team1_score > 99) or (team2_score > 99):
                sizing = 6
            else:
                sizing = 4

            img_draw.text(
                ((W // sizing), bv + h1),
                str(team1_score),
                team1color,
                font=score_font,
                stroke_width=1,
                stroke_fill="black",
            )

            img_draw.text(
                (((W // sizing) * (sizing - 1) - w2), bv + h2),
                str(team2_score),
                team2color,
                font=score_font,
                stroke_width=1,
                stroke_fill="black",
            )
            if not no_desc:
                img_draw.text(
                    (l1, (bv + h2 + h1)), config["desc"], font=desc_font, fill="black"
                )
        else:
            if not no_desc:
                img_draw.text(
                    (l1, (bv + h2)), config["desc"], font=desc_font, fill="black"
                )

        text = Image.new("RGBA", (W, H))

        text_draw = ImageDraw.Draw(text)

        # type checking because sometimes its None sometimes its Nan
        if type(config["team1"]["mascot"]) == str:
            name_mascot_1 = team1r + " " + config["team1"]["mascot"]
        else:
            name_mascot_1 = team1r
        if type(config["team2"]["mascot"]) == str:
            name_mascot_2 = team2r + " " + config["team2"]["mascot"]
        else:
            name_mascot_2 = team2r

        game_text = f"{name_mascot_1}\n Vs.\n {name_mascot_2}\n {gamedate}"

        game_font = simple_size_font_recur(
            text_draw, game_text, W, "Universal_Serif", 50
        )

        text_draw.text((0, 0), game_text, font=game_font, fill="black")

        return bg, text
    else:
        return "prompt failed"


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

    rank1 = config["home_team"]["rank"]

    rank2 = config["away_team"]["rank"]

    if (
        (rank1 is not None) and
        (rank1 is not np.nan) and
        (not pd.isna(rank1))
    ):
        team1r = " #" + str(int(rank1)) + " " + team1
    else:
        team1r = " " + team1

    if (
        (rank2 is not None) and
        (rank2 is not np.nan) and
        (not pd.isna(rank2))
    ):
        team2r = "#" + str(int(rank2))+ " " + team2 + " "
    else:
        team2r = team2 + " "

    prompt = prompt_engineer(
        sport,
        team1full,
        team2full,
        mascot1=config["home_team"]["mascot"],
        mascot2=config["away_team"]["mascot"],
    )

    gamedate = config["game"]["date"]

    logo_buffer = config["logo_buffer"]

    if test:
        bg = Image.new("RGBA", (W, H), color="white")
    else:
        bg = Image.new("RGBA", (W, H))

    main_image = generate_main(
        prompt, config["dalle_key"], test=test, dalle=config["dalle"]
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

        mainfont = size_font_recur(img_draw, team1r, team2r, W, "Freshman", size=150)

        score_font = ImageFont.truetype(
            r"./fonts/Freshman.ttf", size=70, layout_engine=ImageFont.Layout.BASIC
        )

        date_font = ImageFont.truetype(
            r"./fonts/alarm_clock.ttf", size=22, layout_engine=ImageFont.Layout.BASIC
        )  # autosize this

        l1, t1, r1, b1 = img_draw.textbbox((0, img_h), team1r, font=mainfont)

        lv, tv, rv, bv = img_draw.textbbox((r1 + 5, img_h), "VS", font=mainfont)

        l2, t2, r2, b2 = img_draw.textbbox((rv + 5, img_h), team2r, font=mainfont)

        _, _, wd, hd = img_draw.textbbox((0, 0), gamedate, font=date_font)

        _, _, w1, h1 = img_draw.textbbox((0, 0), str(score[0]), font=score_font)

        _, _, w2, h2 = img_draw.textbbox((0, 0), str(score[1]), font=score_font)

        img_draw.text(
            (l1, t1 + lh + 5),
            team1r,
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
            team2r,
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

        # type checking because sometimes its None sometimes its Nan
        if type(config["home_team"]["mascot"]) == str:
            name_mascot_1 = team1r + " " + config["home_team"]["mascot"]
        else:
            name_mascot_1 = team1r
        if type(config["away_team"]["mascot"]) == str:
            name_mascot_2 = team2r + " " + config["away_team"]["mascot"]
        else:
            name_mascot_2 = team2r

        game_text = f"{name_mascot_1}\n Vs.\n {name_mascot_2}\n {gamedate}"

        game_font = simple_size_font_recur(
            text_draw, game_text, W, "Universal_Serif", 75
        )

        text_draw.text((0, 0), game_text, font=game_font, fill="black")

        return bg, text
    else:
        return "Prompt Failed"


def no_caption_image(design_config, main_image):
    bg = Image.new("RGBA", (design_config["W"], design_config["H"]))

    main_image = main_image.resize((design_config["W"], design_config["W"]))
    bg.paste(main_image)

    return bg


def simple_text(design_config, text_in):
    text = Image.new("RGBA", (design_config["W"], design_config["H"]))

    text_draw = ImageDraw.Draw(text)

    game_font = simple_size_font_recur(
        text_draw, text_in, design_config["W"], "Universal_Serif", 75
    )

    text_draw.text((0, 0), text_in, font=game_font, fill="black")

    return text
