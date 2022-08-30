#  Github https://github.com/Northa

from urllib.request import Request, urlopen
import math
from sys import exit
from json import loads

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


def get_validator_votes():

    validator_votes = []
    votes = STATE['result']['round_state']['votes']
    height = STATE['result']['round_state']['height']
    step = STATE['result']['round_state']['step']
    chain = get_chain_id()

    for r_ound in votes:        
        if float(r_ound['precommits_bit_array'].split('=')[-1].strip()) <= 0.66 and float(r_ound['precommits_bit_array'].split('=')[-1].strip()) > 0:
            print(F"\nChain-id: {chain}\n"
                  f"Height: {height} Round: {r_ound['round']} "
                  f"step: {step}\n"
                  f"precommits_bit_array: {r_ound['precommits_bit_array'].split('} ')[-1]}")

            for precommit in r_ound['precommits']:
                try:
                    validator_votes.append(precommit.split('@')[0].split(':')[1].split(' ')[0])
                except IndexError:
                    validator_votes.append(precommit)

        elif float(r_ound['prevotes_bit_array'].split('=')[-1].strip()) <= 0.66 and float(r_ound['prevotes_bit_array'].split('=')[-1].strip()) > 0:
            print(F"\nChain-id: {chain}\nHeight: {height} Round: {r_ound['round']} step: {step}\nprevotes_bit_array: {r_ound['prevotes_bit_array'].split('} ')[-1]}")

            for prevote in r_ound['prevotes']:
                try:
                    validator_votes.append(prevote.split('@')[0].split(':')[1].split(' ')[0])
                except IndexError:
                    validator_votes.append(prevote)

    if len(validator_votes) == 0:
        commit_votes = STATE['result']['round_state']['last_commit']
        height = STATE['result']['round_state']['height']

        if float(commit_votes['votes_bit_array'].split('=')[-1].strip()) > 0.66 :
            print(F"\nChain-id: {chain}\nHeight: {height} Round: {r_ound['round']} step: {step}\nvotes_bit_array: {commit_votes['votes_bit_array'].split('} ')[-1]}")

        for commit_vote in commit_votes['votes']:
            try:
                validator_votes.append(commit_vote.split('@')[0].split(':')[1].split(' ')[0])
            except IndexError:
                validator_votes.append(commit_vote)

    return validator_votes


def get_validators():
    validators = []
    state_validators = STATE['result']['round_state']['validators']['validators']
    for val in state_validators:
        res = val['address'], val['voting_power'], val['pub_key']['value']
        validators.append(res)
    return validators


def get_bonded():
    result = handle_request(REST, '/cosmos/staking/v1beta1/pool')['pool']
    return result


def strip_emoji_non_ascii(moniker):
    # moniker = emoji.replace_emoji(moniker, replace='')
    moniker = "".join([letter for letter in moniker if letter.isascii()])[:15].strip().lstrip()
    return moniker if moniker != "" else "Non_Ascii_Name"


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
                                 "address": validator["operator_address"],
                                 "status": validator["status"],
                                 "voting_power": validator_vp,
                                 "voting_power_perc": f"{vp_percentage}%"}

    return validator_dict, len(validators)


def merge_info():
    print('Bugreports discord: Yep++#9963')
    votes = get_validator_votes()
    validators = get_validators()
    votes_and_vals = list(zip(votes, validators))
    validator_rest, total_validators = get_validators_rest()
    final_list = []

    for k, v in votes_and_vals:
        if v[2] in validator_rest:
            validator_rest[v[2]]['voted'] = k
            final_list.append(validator_rest[v[2]])

    return final_list, total_validators


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


def get_chain_id():
    response = handle_request(REST, 'node_info')
    chain_id = response['node_info']['network']
    return chain_id


def colorize_output(validators):
    result = []
    for num, val in enumerate(validators):
        vp_perc = f"{val['voting_power_perc']:<7}"
        moniker = val['moniker']

        if val['voted'] != 'nil-Vote':
            stat = f"\033[92m{num+1:<3} {'ONLINE':<8} \033[0m"
            result.append(f"{stat} {moniker:<18} {vp_perc}")

        else:
            stat = f"\033[91m{num+1:<3} {'OFFLINE':<8} \033[0m"
            result.append(f"{stat} {moniker:<18} {vp_perc}")

    return result


def calculate_colums(result):
    if len(result) <= 30:
        return list_columns(result, cols=1)
    elif 30 < len(result) <= 100:
        return list_columns(result, cols=2)
    elif 100 < len(result) <= 150:
        return list_columns(result, cols=3)
    else:
        return list_columns(result, cols=4)


def get_pubkey_by_valcons(valcons, height):
    response = handle_request(REST, f"/validatorsets/{height}")
    for validator in response['result']['validators']:
        if valcons in validator['address']:
            return validator['pub_key']['value']


def get_moniker_by_pub_key(pub_key, height):
    response = handle_request(REST, f"cosmos/staking/v1beta1/historical_info/{height}")
    for validator in response['hist']['valset']:

        if pub_key in validator['consensus_pubkey']['key']:
            return strip_emoji_non_ascii(validator['description']['moniker'])


def get_evidence(height):
    evidences = handle_request(REST, '/cosmos/evidence/v1beta1/evidence')
    for evidence in evidences['evidence']:
        if int(height) - int(evidence['height']) < 1000:
            pub_key = get_pubkey_by_valcons(evidence['consensus_address'], evidence['height']).strip()
            moniker = get_moniker_by_pub_key(pub_key, evidence['height'])
            # print(colored(f"Evidence: {moniker}\nHeight: {evidence['height']} {evidence['consensus_address']} power: {evidence['power']}\n", 'yellow'))
            print(f"\033[93mEvidence: {moniker}\nHeight: {evidence['height']} {evidence['consensus_address']} power: {evidence['power']}\033[0m\n")


def main(STATE):
    validators, total_validators = merge_info()

    online_vals = 0
    for num, val in enumerate(validators):
        if val['voted'] != 'nil-Vote':
            online_vals += 1

    print(f"Online: {online_vals}/{total_validators}\n")
    get_evidence(STATE['result']['round_state']['height'])

    result = colorize_output(validators)
    print(calculate_colums(result))


if __name__ == '__main__':
    STATE = handle_request(RPC, 'dump_consensus_state')

    exit(main(STATE))
