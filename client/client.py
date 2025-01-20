import sys
import json
import requests
from utilities.utils import  clear_previous_run, get_ids, cert_prep, check_type, log, ref_payload, check_status, isTOTPExpired, didTOTPFail
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, thread
import argparse
import traceback
from threads.thread_runner import ThreadWrapper
from totp.totp import generate_pass, login_payload
from start.parsing import parse_config, parse_run, parse_run_sup
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
        if(globalenv.verboseMode):
            print("Same TOTP window, using previous token")
        auth_header = {'Authorization': 'Bearer ' + ea_jwt}
        return ea_jwt, auth_header
    try: #if trying refresh without login
        if(globalenv.verboseMode):
            print("New TOTP window, renewing previous token")
        totpCheck = True
        response = ""
        while(totpCheck):
            payload = ref_payload(generate_pass(seed_path), ea_jwt)
            response = requests.post(server_url + '/login', cert=client_cert, json=payload, verify=False)
            if(globalenv.verboseMode):
                print(response.json())
            if isTOTPExpired(response) or didTOTPFail(response):
                totpCheck = True
                print("TOTP Window has already been used. Will retry...")
                time.sleep(30)
            else:
                totpCheck = False
                
        jwt_token = response.json()[1]['accessToken']
        auth_header = {'Authorization': 'Bearer ' + jwt_token}
        return jwt_token, auth_header
    except Exception as e:
        print(e)
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
                    \n- (certify) Certify (Uses IDs from the last run)\
                    \n- (certifyNewOE) Add new OE to existing certificare)\
                    \n- (updatePUD) Sending an updated PUD for an already certified assessment\n\n")
    # New argument added by Yvonne Cliff
    parser.add_argument('--stats_90B_path', default= "jsons/stats_90B.json", help= "Input the path to output 90B statistical results json")
    parser.add_argument('--config_path', default= "jsons/config.json", help="Input the path to your configuration json")
    parser.add_argument('--run_path', default= "jsons/run.json", help= "Input the path to your run json")
    parser.add_argument("-v", "--verbose", action="store_true", help="Run in 'verbose' mode")
    args = parser.parse_args()

    globalenv.verboseMode = args.verbose
    # New global variable stats_90B added by Yvonne Cliff
    globalenv.stats_90B_path = args.stats_90B_path

    run_type = args.run.lower(); config_path = args.config_path; run_path = args.run_path; globalenv.run_path = args.run_path
    check_type(run_type)

    if run_type != "status" or run_type != "certify":
            #Start (remember to change parse try statement)
        client_cert, seed_path, server_url, esv_version = parse_config(config_path)
        log("config_path", config_path)
        assessment_reg, raw_noise, rawNoiseSampleSize, restart_test, restartSampleSize, conditioned, supporting_paths, comments, sdType, mod_id, vend_id, entropyId, oe_id, certify, single_mod, responses, pudEntropyCertificate, pudFilePath, entropyCertificate = parse_run(run_path)
        log("run_path", run_path)

    if run_type == "full":
        # Added by Yvonne Cliff: Erase the stats_file ready for new data:
        with open(globalenv.stats_90B_path, 'w', encoding="utf-8") as stats_file:
            stats_file.close()
        print("*** Entropy Source Validation Client tool startup!")
        clear_previous_run()
        ea = EntropyAssessment(client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, entropyId, oe_id, certify, single_mod)
        ea.login()
        ea.send_reg()
        responseCount=0
        for response in ea.responses:
            ThreadWrapper.runner_data(server_url, response, conditioned[responseCount], raw_noise[responseCount], restart_test[responseCount], client_cert, rawNoiseSampleSize[responseCount],restartSampleSize[responseCount])
            ThreadWrapper.runner_stats(server_url, response, client_cert)
            responseCount = responseCount + 1
        
        certSup = ThreadWrapper.runner_supp(comments, sdType, supporting_paths, server_url, client_cert, ea.auth_header)
        #i = 0
        #for response in ea.responses:
        client_cert, seed_path, server_url, esv_version = parse_config(config_path)
        ea.send_certify(certSup, client_cert, ea.login_jwt, esv_version)
        #    i+=1
        #print("Just ran certify request number ", i)

    if run_type == "fulladdoe":
        # Added by Yvonne Cliff: Erase the stats_file ready for new data:
        with open(globalenv.stats_90B_path, 'w', encoding="utf-8") as stats_file:
            stats_file.close()
        print("*** Entropy Source Validation Client tool startup!")
        clear_previous_run()
        ea = EntropyAssessment(client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, entropyId, oe_id, certify, single_mod)
        ea.login()
        ea.send_reg()
        responseCount=0
        for response in ea.responses:
            ThreadWrapper.runner_data(server_url, response, conditioned[responseCount], raw_noise[responseCount], restart_test[responseCount], client_cert, rawNoiseSampleSize[responseCount],restartSampleSize[responseCount])
            ThreadWrapper.runner_stats(server_url, response, client_cert)
            responseCount = responseCount + 1
        
        certSup = ThreadWrapper.runner_supp(comments, sdType, supporting_paths, server_url, client_cert, ea.auth_header)
        #i = 0
        #for response in ea.responses:
        client_cert, seed_path, server_url, esv_version = parse_config(config_path)
        ea.send_certify_newOE(certSup, client_cert, ea.login_jwt, esv_version, entropyCertificate)
        #    i+=1
        #print("Just ran certify request number ", i)


    #Do a run from the log file
    if run_type == "status":
        # Added by Yvonne Cliff: Erase the stats_file ready for new data:
        with open(globalenv.stats_90B_path, 'w', encoding="utf-8") as stats_file:
            stats_file.close()
        #log_file = json.load(open('jsons\\log.json', 'r'))[0]
        client_cert, seed_path, server_url, esv_version = parse_config(config_path)
        assessment_reg, raw_noise, rawNoiseSampleSize, restart_test, restartSampleSize, conditioned, supporting_paths, comments, sdType, mod_id, vend_id, entropyId, oe_id, certify, single_mod, responses, pudEntropyCertificate, pudFilePath, entropyCertificate = parse_run(run_path)
    
        #print("Logging in...")
        
        #self.login_jwt = login_jwt 
        #self.auth_header = auth_header
        #print("\nLogin Success!")
        if len(responses) > 1:
            print("*** Multiple OE statuses, responses will be batched")
            count = 1
        for response in responses:
            if len(responses) > 1:
                print("*** OE Batch " + str(count))
                count = count + 1
            entr_jwt = response.entr_jwt
            if(globalenv.verboseMode):
                print("Refreshing Token")
            jwt_token, _ = eajwt_refresh(entr_jwt)
            if(globalenv.verboseMode):
                print("\nUsing values from previous run...")

            ea_id = response.ea_id
            df_ids = response.df_ids
            prev_run(server_url, ea_id, df_ids, jwt_token, client_cert)


    #Send Registration and Data Files
    if run_type == "submit":
        clear_previous_run()
        #ea = EntropyAssessment(client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, oe_id, certify, single_mod)
        ea = EntropyAssessment(client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, entropyId, oe_id, certify, single_mod)
        ea.login()
        ea.send_reg()
        responseCount=0
        for response in ea.responses:
            ThreadWrapper.runner_data(server_url, response, conditioned[responseCount], raw_noise[responseCount], restart_test[responseCount], client_cert, rawNoiseSampleSize[responseCount],restartSampleSize[responseCount])
            responseCount = responseCount + 1
            
    #Send Supporting Documentation
    if run_type == "support":
        #ea = EntropyAssessment(client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, oe_id, certify, single_mod)
        ea = EntropyAssessment(client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, entropyId, oe_id, certify, single_mod)
        ea.login()
        certSup = ThreadWrapper.runner_supp(comments, sdType, supporting_paths, server_url, client_cert, ea.auth_header)
        if(globalenv.verboseMode):
            print(certSup)
    
    #Login and certify using log file
    if run_type == "certify":
        print("Using values from previous run..\n")
        #log_file = json.load(open('jsons/log.json', 'r'))[0]
        client_cert, seed_path, server_url, esv_version = parse_config(config_path)
        assessment_reg, raw_noise, rawNoiseSampleSize, restart_test, restartSampleSize, conditioned, supporting_paths, comments, sdType, mod_id, vend_id, entropyId, oe_id, certify, single_mod, responses, pudEntropyCertificate, pudFilePath, entropyCertificate = parse_run(run_path)
        #ea = EntropyAssessment(client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, oe_id, certify, single_mod)
        #i = 0
        #for response in responses:
        ea = EntropyAssessment(client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, entropyId, oe_id, certify, single_mod)
        ea.responses = responses
        ea.login()
        #ea.ea_id = response.ea_id; ea.entr_jwt, _ = eajwt_refresh(response.entr_jwt)  #Uses old ID, refreshes eajwt
        #ea.entr_jwt, _ = eajwt_refresh(response.entr_jwt)
        certSup = ThreadWrapper.runner_supp(comments, sdType, supporting_paths, server_url, client_cert, ea.auth_header)
        ea.send_certify(certSup, client_cert, ea.login_jwt, esv_version)
        #i += 1
            #ea.send_certify(certSup, client_cert, ea.login_jwt, esv_version)



    #Login and send updated certify with new OE
    if run_type == "certifynewoe":
        print("Using values from previous run..\n")
        client_cert, seed_path, server_url, esv_version = parse_config(config_path)
        assessment_reg, raw_noise, rawNoiseSampleSize, restart_test, restartSampleSize, conditioned, supporting_paths, comments, sdType, mod_id, vend_id, entropyId, oe_id, certify, single_mod, responses, pudEntropyCertificate, pudFilePath, entropyCertificate = parse_run(run_path)
        ea = EntropyAssessment(client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, entropyId, oe_id, certify, single_mod)
        ea.responses = responses
        ea.login()
        #ea.ea_id = response.ea_id; ea.entr_jwt, _ = eajwt_refresh(response.entr_jwt)  #Uses old ID, refreshes eajwt
        #ea.entr_jwt, _ = eajwt_refresh(response.entr_jwt)
        certSup = parse_run_sup(run_path)
        #ThreadWrapper.runner_supp(comments, sdType, supporting_paths, server_url, client_cert, ea.auth_header)
        ea.send_certify_newOE(certSup, client_cert, ea.login_jwt, esv_version, entropyCertificate)
        #i += 1
            #ea.send_certify(certSup, client_cert, ea.login_jwt, esv_version)


    #Send updated Supporting Documentation (PUD)
    if run_type == "updatepud":
        if(pudEntropyCertificate == "" or  pudFilePath == ""):
            print("Error: valid Public Use Document information not in run config file")
            sys.exit(1)
        ea = EntropyAssessment(client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, entropyId, oe_id, certify, single_mod)
        ea.login()
        comments = ["Updated PUD"]
        sdType = ["Public Use Document"]
        supporting_paths = [pudFilePath]
        certSup = ThreadWrapper.runner_supp(comments, sdType, supporting_paths, server_url, client_cert, ea.auth_header)
        updateSup = ThreadWrapper.runner_updatedPud(certSup, pudEntropyCertificate, entropyId, pudFilePath, server_url, client_cert, ea.auth_header)

    sys.exit(0) #exit with 0 if program succeeds
