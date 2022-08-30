from module_functions import *
from module_variables import rpc_dict as rpc_dict
import ciso8601
import time

def get_adjacent_height(chain, target_time_secs):

    try:
        request_url = rpc_dict[chain]
        if request_url == "" :
            print("### NO URL : ", chain)
            return

        response = requests.get(request_url+"/block", headers=m_dict["headers"], timeout=m_dict["timeout"])
        data = response.json()
           
        blocktime = 6
        if chain == "BAND": 
            blocktime = 3
        if chain == "EMONEY": 
            blocktime = 30
        if chain == "BINANCE": 
            blocktime = 2
        
        while True : 

            if "error" in data.keys():
                print(chain, data["error"]["data"])
                return chain, data["error"]["data"]

            height = int(data["result"]["block"]["header"]["height"])
            block_time = data["result"]["block"]["header"]["time"]

            ts = ciso8601.parse_datetime(block_time)
            block_time_secs = int(time.mktime(ts.timetuple()))

            diff = block_time_secs - target_time_secs
            abs_diff = abs(diff)

            print (diff, height, block_time)
            if abs_diff <= blocktime :
                return height, block_time

            height_gap = int(abs_diff/blocktime) if abs_diff/blocktime > 1 else abs_diff%blocktime
            next_height = (height-height_gap) if diff > 0 else (height+height_gap)

            search_url = request_url + f"/block?height={int(next_height)}"
            response = requests.get(search_url, headers=m_dict["headers"], timeout=m_dict["timeout"])
            
            data = response.json()   

    except Exception as e:
        print("### Exception : ", chain)
        print(e.__class__.__name__, e)


if __name__ == '__main__':

    # Get Target Start and End Time
    ts = ciso8601.parse_datetime("2022-05-24 00:00")
    start_block_time = int(time.mktime(ts.timetuple()))

    ts = ciso8601.parse_datetime("2022-08-23 00:00")
    end_block_time = int(time.mktime(ts.timetuple()))

    f_result = open("result-heights.csv", "a")
    w_result = csv.writer(f_result)
    
    for chain in rpc_dict.keys():
        if chain not in ["TGRADE"] : 
                
            print(chain)
            print("START HEIGHT")
            s_block_height, s_block_time = get_adjacent_height(chain, start_block_time)

            print("END HEIGHT")
            e_block_height, e_block_time = get_adjacent_height(chain, end_block_time)

            line = (chain, s_block_height, s_block_time, e_block_height, e_block_time)
            w_result.writerow(line)

    f_result.close()
