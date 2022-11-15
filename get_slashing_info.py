from urllib.request import Request, urlopen
import math
from sys import exit
from json import loads
import csv
from module_variables import api_dict as api_dict
ERR_MSG = f"\033[91m[ERR] API endpoint unreachable: api\n" \
          f"[ERR] Be sure you have enabled your API " \
          f"(you can enable this in your app.toml config file)\n" \
          f"Bugreports Discord: Yep++#9963\033[0m"

# default ports
APIS = api_dict

def handle_request(api: str, pattern: str):
    try:
        requestUrl = Request(f"{api}/{pattern}", headers={'User-Agent': 'Mozilla/5.0'})
        response = loads(urlopen(requestUrl).read())
        return response if response is not None else exit(ERR_MSG.replace('api', api))

    except Exception as e:
        print(e)
        exit(ERR_MSG.replace('api', api))


def strip_emoji_non_ascii(moniker):
    # moniker = emoji.replace_emoji(moniker, replace='')
    moniker = "".join([letter for letter in moniker if letter.isascii()])[:15].strip().lstrip()
    return moniker if moniker != "" else "NON_ASCII_NAME"


def get_validators_valcons(REST):
    validator_dict = {}
    validators = handle_request(REST, '/validatorsets/latest')["result"]["validators"]

    for validator in validators:
        address = validator["address"]
        validator_dict[validator["pub_key"]["value"]] = address

    return validator_dict

def get_validators_moniker(REST):
    
    validator_dict = {}
    validators = handle_request(REST, '/cosmos/staking/v1beta1/validators')["validators"]

    for validator in validators:
        moniker = validator["description"]["moniker"][:15].strip()
        moniker = strip_emoji_non_ascii(moniker)
        validator_dict[validator["consensus_pubkey"]["key"]] = moniker

    return validator_dict

def merge_info(REST):

    validators_valcons = get_validators_valcons(REST)
    validator_moniker = get_validators_moniker(REST)
    moniker_dict = {}
    
    for pubkey, address in validators_valcons.items():
        if pubkey in validator_moniker:
            moniker_dict[address] = validator_moniker[pubkey]

    return moniker_dict


def write_csv(chain, data, validators):

    filename_full = "slashing_infos_full.csv"
    filename_jail = "slashing_infos_jail.csv"

    csv_full = []
    csv_jail = []
    csv_full.append(["chain","moniker","valcons","start_height","index_offset","jailed_until","tombstoned","missed_blocks_counter"])
    csv_jail.append(["chain","moniker","valcons","start_height","index_offset","jailed_until","tombstoned","missed_blocks_counter"])
    
    for _, item in enumerate(data["info"]) :
        
        valcons  = item['address']
		
        moniker = ""
        if valcons in validators:
            moniker = validators[valcons]

        start_height = item['start_height']
        index_offset = item['index_offset']
        jailed_until = item['jailed_until']
        tombstoned = item['tombstoned']
        missed_blocks_counter = item['missed_blocks_counter']

        if jailed_until != "1970-01-01T00:00:00Z" :
            csv_jail.append([f"{chain}",f"{moniker}",f"{valcons}",f"{start_height}",f"{index_offset}",f"{jailed_until}",f"{tombstoned}",f"{missed_blocks_counter}"])

        csv_full.append([f"{chain}",f"{moniker}",f"{valcons}",f"{start_height}",f"{index_offset}",f"{jailed_until}",f"{tombstoned}",f"{missed_blocks_counter}"])

    with open(filename_full, 'a') as file:
        writer = csv.writer(file)
        writer.writerows(csv_full)

    with open(filename_jail, 'a') as file:
        writer = csv.writer(file)
        writer.writerows(csv_jail)


if __name__ == '__main__':
    
    for chain, url in APIS.items() :
        data = handle_request(url, '/cosmos/slashing/v1beta1/signing_infos')
        print(chain, data["pagination"]["total"])
        
        validators = merge_info(url)

        write_csv(chain, data, validators)
