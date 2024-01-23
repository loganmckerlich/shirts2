#this is where I input a prompt and it desings that prompt for every school and posts
import argparse
import helpers as hf
import numpy as np
import helpers as hf
import random
import pandas as pd
import time
pd.options.mode.chained_assignment = None

def prompted_run(prompt,title,test=False):
    design_config,shop_config = hf.get_config('rand')
    ify_user = hf.shopify_printify(shop_config,'rand')
    cfbd_loader = hf.cfbp_handler(design_config['cfbd_api'])
    teams = cfbd_loader.get_team_info()

    teams = teams.loc[teams['division'] == 'fbs']
    teams['mascot'] = np.where(teams['mascot'] is None, 'mascot',teams['mascot'])

    teams['prompt_input'] = teams['name']+' '+teams['mascot']+' Mascot'
    all_tm = list(teams['prompt_input'])

    if test:
        randnum = random.randint(0,len(all_tm))
        all_tm = [all_tm[randnum]]
        print(all_tm)
    else:
        print(f'This will cost ${(0.04*len(all_tm))} for {len(all_tm)} schools')
        print(f'This will take minimum {(len(all_tm)*(60/7)/60)+20}mins')
        sample_prompt = prompt.replace('mascot','University of '+ 'Washington Huskies').replace('school','Washington')
        print(f'Sample Prompt: {sample_prompt}')
    for team_mascot in all_tm:
        team = teams.loc[teams.prompt_input==team_mascot].name.values[0]
        print(team)
        # LS = LSU
        # BY = BYU
        # UC = cali schools
        # UA = VAB
        # NC = NC State Wolfpack
        # SM = SMU
        # TC = TCU
        # UM = UMASS
        # US = USC
        # 'UT ' = texas schools
        if (team_mascot[0:2] in ['UC','UN','UA' 'LS','BY','NC','SM','TC','UM','US']) or (team_mascot[0:3] in ['UT ','UTE']):
            full_prompt = prompt.replace('mascot',team_mascot).replace('school',team)
        else:
            full_prompt = prompt.replace('mascot','University of '+team_mascot).replace('school',team)
        main_image = hf.generate_main(
                full_prompt, design_config["dalle_key"], test=test
            )
        # sometimes stuff is blocked by content filter kind of randomly
        if main_image is not None:
            text = hf.simple_text(design_config,team_mascot[0:-7])
            
            image = hf.no_caption_image(design_config,main_image)
            shop_config['image'] = image
            shop_config['title'] = title.replace('school',team).replace('School',team).title()
            shop_config['description'] =  full_prompt + '   ||'+team+'||'
            shop_config['tags'] =  prompt.replace(' ',',')
            shop_config['design'] = image
            shop_config['text'] = text
            ify_user.post(publish=True)
            # at my teir, dalle 3 is limited to 5 images a minute, so i pause for 60/5 seconds to ensure I dont go over that
            time.sleep(60/5)
            

def organize_store(version):
    design_config,shop_config = hf.get_config(version)
    ify_user = hf.shopify_printify(shop_config,version)
    cfbd_loader = hf.cfbp_handler(design_config['cfbd_api'])
    teams = cfbd_loader.get_team_info()

    team_names = list(teams.name)
    # delete all my collections and rebuild them with all products
    ify_user.reset_collections(team_names)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--prompt', help='prompt for design, mascot will be replaced with the mascot from every school',required=True, dest='p')
    parser.add_argument('-t','--title', help='what to name',required=True, dest='t')

    args = parser.parse_args()

    prompted_run(args.p,title = args.t, test=False)
    print(f'Sleeping for 5 mins before organizing store to give time for images to upload')
    time.sleep(60*5)
    organize_store('rand')
    
