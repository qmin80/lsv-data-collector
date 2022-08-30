from module_functions import *
from module_variables import registry_api_dict as ra_dict

chain = ra_dict.keys()
for chain in ra_dict.keys():
    get_validator_info_from_registry(chain)
