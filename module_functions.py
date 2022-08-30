import requests
import pymysql
import csv
from datetime import datetime

from module_variables import module_dict as m_dict
from module_variables import registry_api_dict as ra_dict
from module_variables import api_dict as api_dict
from module_variables import rpc_dict as rpc_dict

lsv_candidates = ["AutoStake", "blockscape", "Bro_n_Bro", "Citadel.One", "Cypher Core", "Frens (", 
                "Genesis Lab", "Klub Staking", "MUS.FACTORY.SHARDNET.NEAR", "polkachu.com", "POSTCAPITALIST", 
                "SkyNet | Validators", "Smart Stake", "StakeLab", "Stakely", "StakeWithUs", "Stakin", "stakr.space", 
                "ushakov", "Valid8"]

def get_validator_info_from_registry(chain):

    try:
        request_url = ra_dict[chain]
        if request_url == "" :
            print("### NO URL : ", chain)
            return

        response = requests.get(request_url, headers=m_dict["headers"], timeout=m_dict["timeout"])
        data = response.json()

        f_result = open("result-registry.csv", "a")
        w_result = csv.writer(f_result)

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

def get_staking_validators(chain): 

    if rpc_dict[chain] == "" or api_dict[chain] == "" :
        print("### NO URL : ", chain)
        return

    try:
        # staing/validators : tendermint_pubkey, operator_address, moniker
        request_url = api_dict[chain] + "/staking/validators"
        print(request_url)
        response = requests.get(request_url, headers={'Content-Type': 'application/json; charset=utf-8'}, timeout=m_dict["timeout"])
        data = response.json()
        
        validators = dict()
        lsv_shortnames = [item[:5] for item in lsv_candidates]

        for item in data["result"]:
            if item["description"]["moniker"].strip()[:5] in lsv_shortnames:    
                pubkey = item["consensus_pubkey"]["value"]
                validators[pubkey] = {}
                validators[pubkey]["operator_address"] = item["operator_address"]
                validators[pubkey]["moniker"] = item["description"]["moniker"]

        # dump_consensus_state : tendermint_pubkey, validator_address, voting_power
        request_url = rpc_dict[chain] + "/dump_consensus_state"
        print(request_url)

        response = requests.get(request_url, headers={'Content-Type': 'application/json; charset=utf-8'}, timeout=m_dict["timeout"])
        data = response.json()

        vlist = data["result"]["round_state"]["validators"]["validators"]
        
        for item in vlist:
            pubkey = item["pub_key"]["value"]
            if pubkey in validators.keys():
                validators[pubkey]["validator_address"] = item["address"]
                validators[pubkey]["voting_power"] = item["voting_power"]

        # validatorsets : tendermint_pubkey, valcons
        request_url = api_dict[chain] + "/validatorsets/latest"
        print(request_url)

        response = requests.get(request_url, headers={'Content-Type': 'application/json; charset=utf-8'}, timeout=m_dict["timeout"])
        data = response.json()  
        
        total = 100
        if "total" in data["result"].keys() :
            total = int(data["result"]["total"])
        
        limit = 100
        page = 1
        offset = 0

        while offset < total  :

            page_url = request_url + f"?page={page}&limit={limit}"
            offset += limit
            page += 1

            response = requests.get(page_url, headers={'Content-Type': 'application/json; charset=utf-8'}, timeout=m_dict["timeout"])
            data = response.json()            

            vlist = data["result"]["validators"]
            for item in vlist:
                pubkey = item["pub_key"]["value"]

                if pubkey in validators.keys():
                    validators[pubkey]["valcons"] = item["address"]


        # validatorsets : tendermint_pubkey, valcons
        request_url = api_dict[chain] + "/cosmos/slashing/v1beta1/signing_infos" # total 확인 후 ?page=3&limit=100
        print(request_url)

        for pubkey in validators.keys():

            valcons = validators[pubkey]["valcons"]
            slashing_url = request_url + f"/{valcons}" 
            response = requests.get(slashing_url, headers={'Content-Type': 'application/json; charset=utf-8'}, timeout=m_dict["timeout"])
            data = response.json()

            validators[pubkey]["jailed_until"] = data["val_signing_info"]["jailed_until"]
        

        # Write to CSV
        f_result = open("result-staking.csv", "a")
        w_result = csv.writer(f_result)
        
        for key in validators.keys():
            
            if "validator_address" not in validators[key].keys() :
                validators[key]["validator_address"] = ""
            
            if "valcons" not in validators[key].keys() :
                validators[key]["valcons"] = ""

            if "voting_power" not in validators[key].keys() :
                validators[key]["voting_power"] = ""

            if "jailed_until" not in validators[key].keys() :
                validators[key]["jailed_until"] = ""

            line = (chain, validators[key]["moniker"].strip(), validators[key]["operator_address"], 
                            validators[key]["validator_address"], validators[key]["valcons"], key, 
                            validators[key]["voting_power"], validators[key]["jailed_until"])
            w_result.writerow(line)    

        f_result.close()

    except Exception as e:
        print("### Exception : ", chain)
        print(e.__class__.__name__, e)
