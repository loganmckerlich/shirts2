from PIL import Image, ImageOps, ImageDraw, ImageFont
from .image_generation import generate_main
import requests


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


def build_design(config, test=False):
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

    if not config["game"]["done"]:
        sfx = "pre"
    else:
        sfx = "post"

    if (not config["game"]["done"]) or (score[0] == score[1]):
        # game unfinished or tie game, nuetral image
        prompt = f"NCAA {sport} {team1full} mascot vs {team2full} mascot"
    elif score[0] > score[1]:
        # home team win
        prompt = f"NCAA {sport} {team1full} mascot beating {team2full} mascot"
    else:  # score[1]>score[0]:
        # away team win
        prompt = f"NCAA {sport} {team1full} mascot getting beaten by {team2full} mascot"

    print(prompt)

    gamedate = config["game"]["date"]

    logo_buffer = config["logo_buffer"]

    if test:
        bg = Image.new("RGBA", (W, H), color="white")
    else:
        bg = Image.new("RGBA", (W, H))

    bg = ImageOps.expand(bg, border=1, fill="black")

    main_image = generate_main(
        config["game_id"], sfx, prompt, config["sd_api"], test=True
    ).resize((iw, ih))

    try:
        logo1 = Image.open(
            requests.get(config["home_team"]["logo"], stream=True).raw
        ).resize((lw, lh))
    except:
        print('failed to get home logo, will use default')
        print(config["home_team"]["logo"])
        logo1 = Image.open(
            requests.get(config["default_logo"], stream=True).raw
        ).resize((lw, lh))

    try:
        logo2 = Image.open(
            requests.get(config["away_team"]["logo"], stream=True).raw
        ).resize((lw, lh))
    except:
        print('Failed to get away logo, will use default')
        print(config["away_team"]["logo"])
        logo2 = Image.open(
            requests.get(config["default_logo"], stream=True).raw
        ).resize((lw, lh))

    img_w, img_h = main_image.size

    # Paste with Coordinates

    offset = ((W - iw) // 2, 0)

    bg.paste(main_image, offset)

    bg.paste(logo1, (0 + logo_buffer, ih))

    bg.paste(logo2, (H - (logo_buffer + 2 * lw), ih))

    img_draw = ImageDraw.Draw(bg)

    mainfont = size_font_recur(img_draw, team1, team2, W, "Freshman", size=150)

    score_font = ImageFont.truetype(
        r"./fonts/Freshman.ttf", size=70, layout_engine=ImageFont.Layout.BASIC
    )

    date_font = ImageFont.truetype(
        r"./fonts/alarm_clock.ttf", size=25, layout_engine=ImageFont.Layout.BASIC
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

    text.save("img1.png", "PNG")

    return bg, text
