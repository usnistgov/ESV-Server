import sys
import json
import requests
from utilities.utils import  clear_previous_run, get_ids, cert_prep, check_type, log, ref_payload, check_status, isTOTPExpired
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, thread
import argparse
from threads.thread_runner import ThreadWrapper
from totp.totp import generate_pass, login_payload
from start.parsing import parse_config, parse_run
from entropy_class import EntropyAssessment
import globalenv

#Disable warnings
from urllib3.exceptions import InsecureRequestWarning, ResponseError
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Monkey patch to force IPv4, since FB seems to hang on IPv6
import socket
old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [response
            for response in responses
            if response[0] == socket.AF_INET]
socket.getaddrinfo = new_getaddrinfo

#Checks TOTP window and refresh jwt if not in previous window 
def eajwt_refresh(ea_jwt, sec = int(time.time() / 30)-1):
    if sec == int(time.time() / 30): #if in same window, keep same token
        print("inside if")
        auth_header = {'Authorization': 'Bearer ' + ea_jwt}
        return ea_jwt, auth_header
    try: #if trying refresh without login
        payload = ref_payload(generate_pass(seed_path), ea_jwt)
        
        totpAlreadyUsed = False
        retries = 0
        response = ""
        while not(totpAlreadyUsed) and retries < 3:
            retries+=1
            response = requests.post(server_url + '/login', cert=client_cert, json=payload, verify=False)
            totpAlreadyUsed = not(isTOTPExpired(response))
            if(not(totpAlreadyUsed)):
                print("TOTP Window has already been used. Retrying...")
                time.sleep(15)
        check_status(response)
        if(globalenv.verboseMode):
            print(response.json())
        jwt_token = response.json()[1]['accessToken']
        auth_header = {'Authorization': 'Bearer ' + jwt_token}

        return jwt_token, auth_header
    except:
        auth_header = {'Authorization': 'Bearer ' + ea_jwt}
        return ea_jwt, auth_header

#Gets stats from previous run
def prev_run(server_url, ea_id, df_ids, jwt_token, client_cert):
    try:
        response = requests.Response
        response.ea_id = ea_id
        response.df_ids = df_ids
        response.entr_jwt = jwt_token

        ThreadWrapper.runner_stats(server_url, response, client_cert)
    except Exception as e:
        if str(e) == "list index out of range":
            print("Error: It is likely that your Entropy Assessment JWT has expired")
        else:
            print(e)
        sys.exit(1)  



if __name__ == "__main__":

    #run is required, but config_path and run_path are not needed when doing runs 2 or 5
    #Therefore, config_path and run_path have -- prefixes
    parser = argparse.ArgumentParser()
    parser.add_argument('run', default="full", help="Choose a run type: \n- (full) Full Run \
                    \n- (status) Check Data File Progress (of last run)\
                    \n- (submit) Submit Entropy Assessment and Data Files \n- (support) Upload Supporting Documentation\
                    \n- (certify) Certify (Uses IDs from the last run) \n\n")
    parser.add_argument('--config_path', default= "jsons/config.json", help="Input the path to your configuration json")
    parser.add_argument('--run_path', default= "jsons/run.json", help= "Input the path to your run json")
    parser.add_argument("-v", "--verbose", action="store_true", help="Run in 'verbose' mode")
    args = parser.parse_args()

    globalenv.verboseMode = args.verbose

    run_type = args.run.lower(); config_path = args.config_path; run_path = args.run_path; globalenv.run_path = args.run_path
    check_type(run_type)

    if run_type != "status" or run_type != "certify":
            #Start (remember to change parse try statement)
        client_cert, seed_path, server_url, esv_version = parse_config(config_path)
        log("config_path", config_path)
        assessment_reg, raw_noise, restart_test, conditioned, supporting_paths, comments, sdType, mod_id, vend_id, entropyId, oe_id, certify, single_mod, responses, itar = parse_run(run_path)
        log("run_path", run_path)

    if run_type == "full":
        print("*** Entropy Source Validation Client tool startup!")
        clear_previous_run()
        ea = EntropyAssessment(client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, entropyId, oe_id, certify, single_mod, itar)
        ea.login()
        ea.send_reg()
        for response in ea.responses:
            ThreadWrapper.runner_data(server_url, response, conditioned, raw_noise, restart_test, client_cert)
            ThreadWrapper.runner_stats(server_url, response, client_cert)
        
        certSup = ThreadWrapper.runner_supp(comments, sdType, supporting_paths, ea.itar, server_url, client_cert, ea.auth_header)
        #i = 0
        #for response in ea.responses:
        client_cert, seed_path, server_url, esv_version = parse_config(config_path)
        ea.send_certify(certSup, client_cert, ea.login_jwt, esv_version)
        #    i+=1
        #print("Just ran certify request number ", i)

    #Do a run from the log file
    if run_type == "status":
        #log_file = json.load(open('jsons\\log.json', 'r'))[0]
        client_cert, seed_path, server_url, esv_version = parse_config(config_path)
        assessment_reg, raw_noise, restart_test, conditioned, supporting_paths, comments, sdType, mod_id, vend_id, entropyId, oe_id, certify, single_mod, responses, itar = parse_run(run_path)
        for response in responses:
            entr_jwt = response.entr_jwt
            print("Refreshing Token"); jwt_token, _ = eajwt_refresh(entr_jwt)
            print("\nUsing values from previous run...")

            ea_id = response.ea_id
            df_ids = response.df_ids
            prev_run(server_url, ea_id, df_ids, jwt_token, client_cert)

    #Send Registration and Data Files
    if run_type == "submit":
        clear_previous_run()
        #ea = EntropyAssessment(client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, oe_id, certify, single_mod)
        ea = EntropyAssessment(client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, entropyId, oe_id, certify, single_mod, itar)
        ea.login()
        ea.send_reg()
        for response in ea.responses:
            ThreadWrapper.runner_data(server_url, response, conditioned, raw_noise, restart_test, client_cert)

    #Send Supporting Documentation
    if run_type == "support":
        #ea = EntropyAssessment(client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, oe_id, certify, single_mod)
        ea = EntropyAssessment(client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, entropyId, oe_id, certify, single_mod, itar)
        ea.login()
        certSup = ThreadWrapper.runner_supp(comments, sdType, supporting_paths, ea.itar, server_url, client_cert, ea.auth_header)
        if(globalenv.verboseMode):
            print(certSup)
    
    #Login and certify using log file
    if run_type == "certify":
        print("Using values from previous run..\n")
        #log_file = json.load(open('jsons/log.json', 'r'))[0]
        client_cert, seed_path, server_url, esv_version = parse_config(config_path)
        assessment_reg, raw_noise, restart_test, conditioned, supporting_paths, comments, sdType, mod_id, vend_id, entropyId, oe_id, certify, single_mod, responses, itar = parse_run(run_path)
        #ea = EntropyAssessment(client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, oe_id, certify, single_mod)
        #i = 0
        #for response in responses:
        ea = EntropyAssessment(client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, entropyId, oe_id, certify, single_mod, itar)
        ea.responses = responses
        ea.login()
        #ea.ea_id = response.ea_id; ea.entr_jwt, _ = eajwt_refresh(response.entr_jwt)  #Uses old ID, refreshes eajwt
        #ea.entr_jwt, _ = eajwt_refresh(response.entr_jwt)
        certSup = ThreadWrapper.runner_supp(comments, sdType, supporting_paths, ea.itar, server_url, client_cert, ea.auth_header)
        ea.send_certify(certSup, client_cert, ea.login_jwt, esv_version)
        #i += 1
            #ea.send_certify(certSup, client_cert, ea.login_jwt, esv_version)

    sys.exit(0) #exit with 0 if program succeeds