from module_functions import *
from module_variables import registry_api_dict as ra_dict

chain = ra_dict.keys()
for chain in ra_dict.keys():
    get_staking_validators(chain)

# TGRADE 는 staking 모듈이 없음
# get_staking_avalidators("TGRADE")
