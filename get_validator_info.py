import requests
import pymysql
import csv
from datetime import datetime

from module_variables import module_dict as m_dict
from module_variables import registry_api_dict as ra_dict
from module_variables import api_dict as api_dict
from module_variables import rpc_dict as rpc_dict

lsv_candidates = ["AutoStake", "BlockHunters", "Bro_n_Bro", "Citadel.One", "Chorus One", "JustLuck", 
                "Genesis Lab", "Klub Staking", "Legion Nodes", "polkachu.com", "Matrixed.Link", 
                "Oldcat", "StakeLab", "Stakely", "StakeWithUs", "Stakin"]

def get_validator_info_from_registry(chain):

    try:
        request_url = ra_dict[chain]
        if request_url == "" :
            print("### NO URL : ", chain)
            return

        response = requests.get(request_url, headers=m_dict["headers"], timeout=m_dict["timeout"])
        data = response.json()

        f_result = open("result-vinfo.csv", "a")
        w_result = csv.writer(f_result)
        
        line = ("chain", "rank", "tokens", "jailed_until", "moniker", "operator_address", "hex_address")
        w_result.writerow(line)
        
        lsv_shortnames = [item[:7] for item in lsv_candidates]

        for item in data["validators"] :

            if item["moniker"].strip()[:7] in lsv_shortnames:
                
                if "signing_info" not in item.keys() :
                    item["signing_info"]["jailed_until"] = ""
                
                line = (chain, item["rank"], item["tokens"], item["signing_info"]["jailed_until"], item["moniker"].strip(), item["operator_address"], item["hex_address"])
                w_result.writerow(line)

        f_result.close()

    except Exception as e:
        print("### Exception : ", chain)
        print(e.__class__.__name__, e)


chain = ra_dict.keys()
for chain in ra_dict.keys():
    get_validator_info_from_registry(chain)

