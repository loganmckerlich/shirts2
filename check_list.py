import helpers as hf
import yaml
from unidecode import unidecode

with open("info/2024_qualifiers.yml", "r") as f:
    qualifiers = yaml.safe_load(f)
design_config, shop_config = hf.get_config("cbb")
main_config = hf.combine_configs(design_config, shop_config)
ify_user = hf.shopify_printify(main_config, "cbb")
cfbd_loader = hf.cfbp_handler(main_config["cfbd_api"])

teams = cfbd_loader.get_team_info()
teams["joiner"] = teams.name.apply(lambda x: unidecode(x).lower())



if __name__ == '__main__':
    for team in qualifiers:
        tjoiner = unidecode(team).lower()
        team_info = teams.loc[teams.joiner==tjoiner].to_dict("records")
        if len(team_info)==0:
            print(f'missing {team}')
        elif (team_info[0]['mascot']==None) or (team_info[0]['color']==None)or(team_info[0]['logos'] == None) :
            print(f'Incomplete {team}')