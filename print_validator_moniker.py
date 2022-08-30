from urllib.request import Request, urlopen
import math
from sys import exit
from json import loads
import csv

ERR_MSG = f"\033[91m[ERR] API endpoint unreachable: api\n" \
          f"[ERR] Be sure you have enabled your API " \
          f"(you can enable this in your app.toml config file)\n" \
          f"Bugreports Discord: Yep++#9963\033[0m"

# default ports
REST = "https://lcd-juno.itastakers.com"
RPC = "https://rpc-juno.itastakers.com"


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
    return moniker if moniker != "" else "Non_Ascii_Name"


def get_validators():
    validators = []
    state_validators = STATE['result']['round_state']['validators']['validators']
    for val in state_validators:
        res = val['address'], val['voting_power'], val['pub_key']['value']
        validators.append(res)
    return validators


def get_validators_rest():
    bonded_tokens = int(get_bonded()["bonded_tokens"])
    validator_dict = {}
    validators = handle_request(REST, '/staking/validators')["result"]

    for validator in validators:
        validator_vp = int(int(validator["tokens"]))
        vp_percentage = round((100 / bonded_tokens) * validator_vp, 3)
        moniker = validator["description"]["moniker"][:15].strip()
        moniker = strip_emoji_non_ascii(moniker)
        validator_dict[validator["consensus_pubkey"]["value"]] = {
                                 "moniker": moniker,
                                 "operator_address": validator["operator_address"],
                                 "status": validator["status"],
                                 "voting_power": validator_vp,
                                 "voting_power_perc": f"{vp_percentage}%"}

    return validator_dict, len(validators)

def merge_info():

    validators = get_validators()
    validator_rest, total_validators = get_validators_rest()
    final_list = []

    for v in validators:
        if v[2] in validator_rest:
            validator_rest[v[2]]['address'] = v[0]
            final_list.append(validator_rest[v[2]])

    return final_list, total_validators


def get_chain_id():
    response = handle_request(REST, 'node_info')
    chain_id = response['node_info']['network']
    return chain_id


def get_bonded():
    result = handle_request(REST, '/cosmos/staking/v1beta1/pool')['pool']
    return result


def colorize_output(validators):
    result = []
    csv_result = []

    result.append("validator_address\tmoniker\tvoting_power\tvoting_power_perc\toperator_address")
    csv_result.append(["validator_address","moniker","voting_power","voting_power_perc","operator_address"])

    for num, val in enumerate(validators):
        validator_address = val['address']
        moniker = val['moniker']
        voting_power = val['voting_power']
        voting_power_perc = val['voting_power_perc']
        operator_address = val['operator_address']

        result.append(f"{validator_address}\t{moniker:<18}\t{voting_power}\t{voting_power_perc}\t{operator_address}")
        csv_result.append([f"{validator_address}",f"{moniker}",f"{voting_power}",f"{voting_power_perc}",f"{operator_address}"])

    return result, csv_result


def calculate_colums(result):
        return list_columns(result, cols=1)


def list_columns(obj, cols=3, columnwise=True, gap=8):
    # thnx to https://stackoverflow.com/a/36085705

    sobj = [str(item) for item in obj]
    if cols > len(sobj): cols = len(sobj)
    max_len = max([len(item) for item in sobj])
    if columnwise: cols = int(math.ceil(float(len(sobj)) / float(cols)))
    plist = [sobj[i: i+cols] for i in range(0, len(sobj), cols)]
    if columnwise:
        if not len(plist[-1]) == cols:
            plist[-1].extend(['']*(len(sobj) - len(plist[-1])))
        plist = zip(*plist)
    printer = '\n'.join([
        ''.join([c.ljust(max_len + gap) for c in p])
        for p in plist])
    return printer


def main(STATE):
    validators, total_validators = merge_info()

    result, csv_result = colorize_output(validators)
    print(calculate_colums(result))

    filename = get_chain_id() + "_monikers.csv"    
    with open(filename, 'w') as file:
        writer = csv.writer(file)
        writer.writerows(csv_result)
        
if __name__ == '__main__':
    STATE = handle_request(RPC, 'dump_consensus_state')

    exit(main(STATE))
