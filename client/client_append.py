import argparse
import globalenv
from utilities.utils import add_to_prev_run
import sys
import json
import requests

# Author: Yvonne Cliff
#
# Function parse_prev_run is a cut down version of parse_run from parsing.py
#
# The main function copies "PreviousRun" data from the toAppend_path 
# and appends it to the "PreviousRun" data already in the run_path
#
# The purpose is to combine entropy assessments with different certificates for the conditioning function
# and which were therefore submitted using different run_path and metadata files
# into one certify request.

def parse_prev_run(run_path):
    try:
        run_file = open(run_path, 'r')
        run_file = json.load(run_file)

        responseList = []
        if "PreviousRun" in run_file[0]:
            if(globalenv.verboseMode):
                print('PreviousRun detected')
            for eachRun in run_file[0]["PreviousRun"]:
                res = requests.Response()
                res.entr_jwt = eachRun["entr_jwt"]
                res.df_ids = eachRun["df_ids"]
                res.ea_id = eachRun["ea_id"]
                # The supporting document info only goes in the first item in PreviousRun. No need to add it
                # to others because the info is the same
                if "cert_supp" in run_file[0]["PreviousRun"][0]:
                    res.cert_supp = run_file[0]["PreviousRun"][0]["cert_supp"]
                else:
                    res.cert_supp = ""
                responseList.append(res)
            if(globalenv.verboseMode):
                print('PreviousRun parsed')
        else:
            if(globalenv.verboseMode):
                print('No PreviousRun detected')

        if(globalenv.verboseMode):
            print('Run file successfully parsed')
        return responseList

    except Exception as e:
        print("There was an error parsing file ", run_path, " Please try again")
        print("Error parsing: ", e)
        sys.exit(1)


if __name__ == "__main__":


    parser = argparse.ArgumentParser()
    parser.add_argument('--toAppend_path', help="Input the path to a Json with previous runs you want appended to the run_path")
    parser.add_argument('--run_path', default= "jsons/run.json", help= "Input the path to your run json")
    parser.add_argument("-v", "--verbose", action="store_true", help="Run in 'verbose' mode")
    args = parser.parse_args()

    globalenv.verboseMode = args.verbose

    toAppend_path = args.toAppend_path; run_path = args.run_path; globalenv.run_path = args.run_path

    print("\nReading previous run data from ", toAppend_path, "...")
    responses_toAppend = parse_prev_run(toAppend_path)

    if(globalenv.verboseMode):
        print("\nReading previous run data from ", run_path, "...")
        responses_existing = parse_prev_run(run_path)

    print("\nAppending previous run data from ", toAppend_path, " into ", run_path)

    if(globalenv.verboseMode):
        print("**************Existing previous run data in ", run_path)
        print("[")
        for response in responses_existing:
            print("{\"ea_id\":", response.ea_id, "\n \"df_ids\":", response.df_ids, "\n \"entr_jwt\":", response.entr_jwt, "\n \"cert_supp\":", response.cert_supp, "\n},")
        print("]")
        print("\n*********************Extra responses to append from ", toAppend_path)
        print("[")
        for response in responses_toAppend:
            print("{\"ea_id\":", response.ea_id, "\n \"df_ids\":", response.df_ids, "\n \"entr_jwt\":", response.entr_jwt, "\n \"cert_supp\":", response.cert_supp, "\n},")
        print("]")

        print("\n*********************\n")

    for response in responses_toAppend:
        add_to_prev_run(response)

    print("\nFinished updating ", run_path)    

    if(globalenv.verboseMode):    
        print("\nReading ", run_path, " so that result can be output...")
        responses_existing = parse_prev_run(run_path)

        print("\n**************All previous run data now in ", run_path)
        print("[")
        for response in responses_existing:
            print("{\"ea_id\":", response.ea_id, "\n \"df_ids\":", response.df_ids, "\n \"entr_jwt\":", response.entr_jwt, "\n \"cert_supp\":", response.cert_supp, "\n},")
        print("]")
        print("\n*****************End Previous Run Data")