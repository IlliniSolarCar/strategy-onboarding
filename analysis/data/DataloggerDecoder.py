#!/usr/bin/env python
# coding: utf-8


#EXAMPLE: 
#   cd analysis/data
#   python3 DataloggerDecoder.py -i datalogger_fsgp2022_day1/raw -o datalogger_fsgp2022_day1/decoded

import numpy as np
import csv
import json
import glob
from tqdm import tqdm
import argparse
from datetime import datetime
import pandas as pd

data_types = {
    "FloatLE": {"type": "float", "byteLen": 4, "fstring": ">f"},
    "Uint16LE": {"type": "int", "byteLen": 2, "isSigned": False, "fstring": ">u2"},
    "Int16LE": {"type": "int", "byteLen": 2, "isSigned": True, "fstring": ">i2"},
    "Uint32LE": {"type": "int", "byteLen": 4, "isSigned": False, "fstring": ">u4"},
    "Int32LE": {"type": "int", "byteLen": 4, "isSigned": True, "fstring": ">i4"},
    "Uint64LE": {"type": "int", "byteLen": 8, "isSigned": False, "fstring": ">u8"},
    "Int64LE": {"type": "int", "byteLen": 8, "isSigned": True, "fstring": ">i8"},
    "Uint8LE": {"type": "int", "byteLen": 1, "isSigned": False, "fstring": "B"},

    "BitMap8LE": {"type": "bitmap", "byteLen":1},
    "BitMap16LE": {"type": "bitmap", "byteLen":2},
    "BitMap32LE": {"type": "bitmap", "byteLen":4}
}

def decode_bitmap(data, length):
    def access_bit(data, num):
        base = int(num // 8)
        shift = int(num % 8)
        return (data[base] & (1<<shift)) >> shift
    
    return [access_bit(data, i) for i in range(length * 8)]

def get_message_len(can_id, canDef):
    can_struct = canDef[can_id]
    if isinstance(can_struct["DataFormat"], list):
        l = 0
        for i in range(can_struct["DataQty"]):
            l += data_types[can_struct["DataFormat"][i]]["byteLen"]
    else:
        l = (data_types[can_struct["DataFormat"]]["byteLen"] * can_struct["DataQty"])
    return l

def decode_array(hexString, can_id, canDef, dformat, dquantity):
    l = get_message_len(can_id, canDef)
    byte_array = bytes.fromhex(hexString)[-l:]
    cur_index = 0
    ret = []
    for i in range(dquantity):
        if isinstance(dformat, list):
            this_format = dformat[i]
        else:
            this_format = dformat
        dtype = data_types[this_format]
        b = byte_array[cur_index:cur_index + dtype["byteLen"]]
        if(dtype["type"] == "int"):
            ret.append(int(np.ndarray(shape=(1,),dtype=dtype["fstring"], buffer=b)[0]))
        elif(dtype["type"] == "float"):
            ret.append(float(np.ndarray(shape=(1,),dtype=dtype["fstring"], buffer=b)[0]))
        else:
            ret.append(decode_bitmap(b, dtype["byteLen"]))
        
        cur_index += dtype["byteLen"]
    return ret
        
def decode(file,canDef):
    messages = []
    with open(file) as fp:

        next(fp) #Mount
        next(fp) #RTC Time Good
        
        time_row = next(fp)
        start_millis = datetime.strptime(time_row[-20:-1], '%Y-%m-%d %H:%M:%S').timestamp() * 1000
        print(f"start millis: {start_millis}")

        next(fp) #SD mount time

        # print(fp)
        dlreader = csv.DictReader(fp, delimiter=',')
        for row in tqdm(dlreader):
            try:
                msg = {
                    "millis": int(row["millis"]) + int(start_millis),
                    "id": row["id"],
                    "hexString": row["data"]
                }
                can_struct = canDef[row["id"]]
            except:
                print("Can Message ID not found, skipping.", row)
                continue
            
            try:
                parsedValue = decode_array(row["data"], row["id"], canDef, can_struct["DataFormat"], can_struct["DataQty"])
            except Exception as e:
                print("Caught exception for row", row, e)
            
            if "Multiplier" in can_struct and row["id"]!='0x5E4':
                if isinstance(can_struct["Multiplier"], list):
                    for i in range(len(parsedValue)):
                        parsedValue[i] *= can_struct["Multiplier"][i]
                else:
                    for i in range(len(parsedValue)):
                        parsedValue[i] *= can_struct["Multiplier"]
            msg["length"] = len(parsedValue)
            msg["parsedValue"] = parsedValue
            
            messages.append(msg)
    return messages


def decode_folder(input_folder, output_folder, canDef):
    files = glob.glob(input_folder +"/*.csv")
    print(f"\n decoding {len(files)} files from {input_folder} \n")
    for file in tqdm(files):
        # print(file)
        messages = decode(file, canDef)

        # json.dump(messages, fp, indent=4)

        df = pd.DataFrame.from_dict(messages)

        date = datetime.fromtimestamp(messages[0].get("millis")/1000.0)
        date = date.strftime('%Y-%m-%d_%H-%M-%S')

        df.to_csv(output_folder + "/" + str(date) + '.csv', index = False, header=True)
    
    
    # elif(args.database):
    #     client = pymongo.MongoClient(args.host, 27017)
    #     db = client["solarcar"]
    #     collection = db["messages"]
    #     collection.insert_many(messages)
    #     collection.insert_many(messages)

def main():
    parser = argparse.ArgumentParser(description='Decode data logger data')
    parser.add_argument("-i", "--input", type=str, required=True, help='input data logger file')
    parser.add_argument("-o", "--output", type=str, help='output file')
    parser.add_argument("-d", "--database", action="store_true", help="write output to a database")
    parser.add_argument("--host", type=str, default="localhost", help="Host name of database")
    parser.add_argument("--can", type=str, default="./canDef.json", help="Path to CAN def json")
    args = parser.parse_args()

    if (not args.database) and (args.output == None):
        print("Must either specify output file or database.")
        quit()

    canDefPath = args.can
    with open(canDefPath) as fp:
        canDef = json.load(fp)

    decode_folder(args.input, args.output, canDef)
    

if __name__ == "__main__":
    main()
    
