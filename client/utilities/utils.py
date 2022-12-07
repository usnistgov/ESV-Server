import sys
import json
from cryptography.hazmat.primitives import hashes, hmac
import time
import base64
import requests
import utilities.esvutil as esvutil
import sys
import requests
import globalenv
import traceback
import os.path

from urllib3.exceptions import InsecureRequestWarning, ResponseError
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

#Generates payload for JWT refresh
def ref_payload(passw, jwt):

    totp = [
        {'esvVersion': '1.0'},
        {'password': passw,
        'accessToken': jwt
        }
    ]
    #totp = json.dumps(totp)
    return totp #Should return as single-line string, not JSON

#Checks that parseRun uses
def run_checks(comments, sdType, supporting_paths):
    if len(comments) < len(supporting_paths):
        print("Error: Supporting Documentation Comments array must be the same length as that of the supporting file paths")
        sys.exit(1)
    if len(sdType) < len(supporting_paths):
        print("Error: Supporting Documentation Types array must be the same length as that of the supporting file paths")

#Gets and prints eaIDs and dfIDs after sending registration
def get_ids(response):
    dfIDs = []
    eaIDresponse = response['url']
    eaID = ""
    index = eaIDresponse.rfind("/")
    for j, c in enumerate(eaIDresponse[index:]):
        if c.isdigit():
            eaID = eaIDresponse[index:][j:]
            break
    print("\nEntropy Assessment Registration ID: " + eaID)

        #dfIDs (possibly add the type of file in the future)
    print("Data file IDs for " + eaID + " are: ")
    
    for i in response['dataFileUrls']: #handling JSON structure
        urls = list(i.values())
        index = urls[0].rfind("/")
        urls[0] = urls[0][index:]

        for j, c in enumerate(urls[0]):
            if c.isdigit():
                urls[0] = urls[0][j:]
                break
        ids = list(i.keys())
        if len(urls) <= 1: #accounting for sequencePosition in conditionedBits IDs
            print(ids[0] + ": " + urls[0]) 
        else:
            print(ids[0] + ", "+ ids[1] + " " + str(urls[1]) + ": " + str(urls[0]))
        
        dfIDs.append(urls[0])
    return eaID, dfIDs

def cert_prep(certify, certSup, esv_version, singleMod, modId, vendId, entropyId, eaID, oeId, entrjwt, itar): #  *Also uses other variables defined in main
    
    certify[0]["esvVersion"] = esv_version
    certEntropy = certify[1]["entropyAssessments"][0]
    certEntropy["accessToken"] = entrjwt     #Will need to change to a loop (like supp) if implementing >1 assessment
    certEntropy["oeId"] = oeId
    certEntropy["eaId"] = int(eaID) 

    certify[1]["itar"] = itar #assessment_reg[1]["itar"]
    certify[1]["limitEntropyAssessmentToSingleModule"] = singleMod
    certify[1]["moduleId"] = modId
    certify[1]["vendorId"] = vendId
    certify[1]["entropyId"] = entropyId #int(eaID) #entropyId
    
    for info in reversed(certSup): #add supporting document IDs and JWTs
        certify[1]["supportingDocumentation"].append(info[0])
    
    return certify

def check_type(run_type):
    accepted = ["full", "status", "submit", "support", "certify"]
    if run_type not in accepted:
        print("Error: Run type is not listed in possible runs")
        sys.exit(1)

    
def log(name, value):
    try:
        if not os.path.exists("jsons/log.json"):
            create_log_file()
        with open('jsons/log.json', 'r+') as f:
            log_file = json.load(f)
            if log_file[0][name] == value:
                f.close()
                return
            log_file[0][name] = value
            f.seek(0)
            json.dump(log_file, f, indent=4)
            f.truncate() #prevents log error bugs
        accepted = ["entr_jwt", "df_ids", "ea_id", "cert_supp"]
        if name in accepted:
            with open(globalenv.run_path , "r+") as f2:
                run_file = json.load(f2)
                if "PreviousRun" not in run_file[0]:
                    run_file[0]["PreviousRun"] = {}
               
                #if run_file[0]["PreviousRun"][name] == value:
                #    f2.close()
                #    return
                #print("current " + run_file[0]["PreviousRun"][name])
                # TODO: Document that previous run only goes in first previous run
                run_file[0]["PreviousRun"][0][name] = value
                f2.seek(0)
                json.dump(run_file, f2, indent=4)
                f2.truncate()
    except Exception as e:
        traceback.print_exc()
        print("Exception: ")
        print(e.with_traceback)

def clear_previous_run():
    with open(globalenv.run_path , "r+") as f2:
        run_file = json.load(f2)
        if "PreviousRun" in run_file[0]:
            del run_file[0]["PreviousRun"]
            f2.seek(0)
            json.dump(run_file, f2, indent=4)
            f2.truncate()

def add_to_prev_run(response):
    try:
        with open(globalenv.run_path , "r+") as f2:
            run_file = json.load(f2)
            if "PreviousRun" not in run_file[0]:
                #print("New PreviousRun")
                run_file[0]["PreviousRun"] = []
         
            #run_file[0]["PreviousRun"].dumps({"Run":{"ea_id" + response.ea_id}})
            #print(json.dumps({"name": "John", "age": 30}))
            run = run_file[0]["PreviousRun"].append({"ea_id":response.ea_id, "df_ids":response.df_ids, "entr_jwt":response.entr_jwt})
            #jsobj["a"]["b"]["e"].append({"f":var3, "g":var4, "h":var5})
            #run = "test"
            #run["ea_id"] = response.ea_id
            #run["df_ids"] = response.df_ids
            #run["entr_jwt"] = response.entr_jwt

            f2.seek(0)
            json.dump(run_file, f2, indent=4)
            f2.truncate()
    except Exception as e:
        traceback.print_exc()
        print("Exception: ")
        print(e.with_traceback)

def add_cert_supp_to_prev_run(ea_id, cert_supp):
    with open(globalenv.run_path , "r+") as f2:
        run_file = json.load(f2)
        previousRuns = run_file[0]["PreviousRun"]
        for previousRun in previousRuns:
            if previousRun["ea_id"] == ea_id:
                previousRun["cert_supp"] = cert_supp
                return

#Checks the status code of a response and exits with a 1 if error is 400s or 500s
# Also prints error message        
def check_status(response):
    if int(response.status_code) / 100 >= 4:
        try:
            print("Error: Status code " + str(response.status_code))
            print(response.json())
            sys.exit(1)
        except:
            sys.exit(1)

def isTOTPExpired(response):
    if int(response.status_code) != 403:
        return False
    responseJson = response.json()
    errorMsg = responseJson[1]["error"]

    print(errorMsg.lower())
    if "totp" in errorMsg.lower() and "window" in errorMsg.lower():
        return True
    return False

def create_log_file():
    f = open('jsons/log.json',"w")
    f.write("[{\"entr_jwt\": \"placeholder\",\"df_ids\": [\"1\",\"2\"],\"ea_id\": \"1\",\"server_url\": \"https://demo.esvts.nist.gov:7443/esv/v1\",\"client_cert\": [\"ESVTest.cer\",\"ESVTest.key\"],\"config_path\": \"config.json\",\"run_path\": \"run.json\",\"cert_supp\": [[{\"sdId\": 1,\"accessToken\": \"placeholder\"}]]}]")
    f.close()
