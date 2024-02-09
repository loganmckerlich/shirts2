# Everygame March Madness

## Whats This?
I was watching college football one day and enjoyed the game so much I bought a shirt to remember the moment. This was possible as it was a big CFP game. I was thinking about how if I went to a smaller school, or even was just excited about a less big game, there probably wouldnt be a shirt I could buy for that specific game. That inspired me to build a website to sell shirts for every game of the college football season. That being said as the football game I was excited about was playoffs, the CFB season is over, so I decided to build this for march madness.

## Whats inside:
    - shopify API manipulation
    - printify API manipulation
    - Dalle-3 API integration
    - Basketball reference web scrapper
    - Basically this runs an entire backend of generating images and posting shirts with those images

## What does what?
    - CBB_shirts.py 
        - makes a shirt for every game that happened yesterday, including final scores
        - makes a shirt for every game that will happen today, obviously no scores
        - publishes all that stuff in printify, and then posts it to sell on shopify
        - organizes a shopify store into collections by team
        - this is tested and built out it works (as of feb 2024)
    - CFB_shirts.py
        - WIP
        - going to do same as CBB but on a weekly basis as football schedules are planned farther ahead that march madness schedules
    - random_shirts.py
        - the idea here is more generic shirts, I give it a prompt and it generates a shirt with that on it for every (d1? FBS? I havent decided but basically just a bunch) school

## Is this a business?
The margins arent great as I outsource all of the inventory managmeent and stuff. However I am hoping that I make enough money to cover my API costs and shopify fees. Well see.