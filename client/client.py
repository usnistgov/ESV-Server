import sys
from authentication.login import login
from client_actions import certify_entropy_assessment, certify_update_public_use_document, clear_history, register_entropy_assessment, submit_supporting_documentation
from request_types.certificates import send_get_entropy_certificate
import argparse
from utilities.parsing import parse_config, parse_run
#from rbg_class import RandomBitGenerator
#from combined_ea_rbg import Combined_EntropyAssessment_RBG
import globalenv
import requests


# Disable warnings
from urllib3.exceptions import InsecureRequestWarning
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


# Gets stats from previous run
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

    # run is required, but config_path and run_path are not needed when doing runs 2 or 5
    # Therefore, config_path and run_path have -- prefixes
    parser = argparse.ArgumentParser()
    parser.add_argument('run', default="full", help="Choose a run type:\
                    \n- (full) Full run of an initial entropy source submission\
                    \n- (fullAddOE) Full run to add an OE to an existing entropy source certificate\
                    \n- (status) Check Data File Progress (of last run)\
                    \n- (submit) Submit Entropy Assessment and Data Files\
                    \n- (support) Upload Supporting Documentation\
                    \n- (submitRBG) Submit Random Bit Generator\
                    \n- (submitRBG_EA) Submit both an Entropy Assessment and Random Bit Generator\
                    \n- (certify) Certify an Entropy Assessment (Uses IDs from previous run)\
                    \n- (certifyRBG) Certify an RBG (Uses IDs from previous run)\
                    \n- (certifyNewOE) Add new OE to existing entropy source certificate)\
                    \n- (getCertificate) Get completed entropy source or random bit generator certificate (needs certificateID)\
                    \n- (updatePUD) Update the PUD for an already certified entropy source\n\n")
    
    # TODO add option to refresh all access tokens in a run file

    parser.add_argument('--stats_90B_path', default="", help= "Output file for 90B statistical results json")
    parser.add_argument('--config_path', help="Input the path to your configuration json")
    parser.add_argument('--run_path', help= "Input the path to your run json")
    parser.add_argument("-v", "--verbose", action="store_true", help="Run in 'verbose' mode")
    parser.add_argument('--certificateID', help="The number of the certificate requested")
    args = parser.parse_args()

    # Set up globals based on command line arguments
    globalenv.verboseMode = args.verbose
    
    if args.stats_90B_path == "":
        globalenv.record_90B_stats = False
    else:
        globalenv.record_90B_stats = True
        globalenv.stats_90B_path = args.stats_90B_path

    globalenv.run_path = args.run_path
    parse_run(args.run_path)        # Sets globalenv.run_data
    parse_config(args.config_path)  # Sets globalenv config properties

    # Define the actions that will occur for this run
    flags = {
        "clear_history": False,
        "ea_registration": False,
        "supporting_document_upload": False,
        "ea_certify": False,
        "ea_add_oe_certify": False,
        "update_pud_certify": False,
        "get_entropy_certificate": False
    }

    # Perform a login
    login()

    # Determine actions based on run type
    run_type = args.run.lower()

    if run_type == "full":              # A complete entropy source submission
        flags["clear_history"] = True
        flags["ea_registration"] = True
        flags["supporting_document_upload"] = True
        flags["ea_certify"] = True

    elif run_type == "submit":          # Register an entropy source and upload data files
        flags["clear_history"] = True
        flags["ea_registration"] = True
    
    elif run_type == "support":         # Upload supporting documentation
        flags["clear_history"] = True
        flags["supporting_document_upload"] = True

    elif run_type == "certify":         # Certify a previously registered entropy source
        flags["ea_certify"] = True

    elif run_type == "fulladdoe":       # Add an OE to an existing validated entropy source
        flags["clear_history"] = True
        flags["ea_registration"] = True
        flags["supporting_document_upload"] = True
        flags["ea_add_oe_certify"] = True

    elif run_type == "certifynewoe":    # Add an OE to an existing entropy source certificate
        flags["ea_add_oe_certify"] = True

    elif run_type == "updatepud":       # Update the Public Use Document on an existing entropy source certificate
        flags["supporting_document_upload"] = True
        flags["update_pud_certify"] = True

    elif run_type == "status":          # Check the status of previously submitted data files

        # TODO
        # Added by Yvonne Cliff: Erase the stats_file ready for new data:
        with open(globalenv.stats_90B_path, 'w', encoding="utf-8") as stats_file:
            stats_file.close()

        assessment_reg, raw_noise, rawNoiseSampleSize, restart_test, restartSampleSize, conditioned, supporting_paths, comments, sdType, mod_id, vend_id, entropyId, oe_id, certify, single_mod, responses, pudEntropyCertificate, pudFilePath, entropyCertificate = parse_run(run_path)
    
        if len(responses) > 1:
            print("*** Multiple OE statuses, responses will be batched")
            count = 1
        for response in responses:
            if len(responses) > 1:
                print("*** OE Batch " + str(count))
                count = count + 1
            entr_jwt = response.entr_jwt
            if globalenv.verboseMode:
                print("Refreshing Token")
            jwt_token, _ = eajwt_refresh(entr_jwt)
            if globalenv.verboseMode:
                print("\nUsing values from previous run...")

            ea_id = response.ea_id
            df_ids = response.df_ids
            prev_run(server_url, ea_id, df_ids, jwt_token, client_cert)

        exit(0)

    elif run_type == "getcertificate":  # View an entropy source certificate
        flags["get_entropy_certificate"] = True

        # Get certificate number to look up
        certificateLookupID = args.certificateID

        if certificateLookupID == None:
            print("Error: Certificate ID not provided. Use --certificateID [ID] on commandline to set. For example --certificateID E0\n")
            exit(1)

        send_get_entropy_certificate(certificateLookupID)
        
        exit(0)

    # Register a random bit generator
    elif run_type == "submitrbg":
        
        # TODO
        clear_previous_run()
        #ea = EntropyAssessment(client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, oe_id, certify, single_mod)
        random_bit_generator_reg = loadObject(run_path[0]["RandomBitGeneratorRegistrationPath"])
        rbg = RandomBitGenerator(client_cert, server_url, random_bit_generator_reg, seed_path, mod_id, vend_id, entropyId, oe_id, certify, single_mod)
        rbg.login()
        rbg.send_reg()
        responseCount=0
        #for response in rbg.responses:
            # TODO
        #    ThreadWrapper.runner_data(server_url, response, conditioned[responseCount], raw_noise[responseCount], restart_test[responseCount], client_cert, rawNoiseSampleSize[responseCount], restartSampleSize[responseCount])
        #    ThreadWrapper.runner_stats(server_url, response, client_cert)
        #    responseCount = responseCount + 1
        exit(0)

    # Register a random bit generator and entropy source with data files
    elif run_type == "submitrbg_ea":

        # TODO
        clear_previous_run()
        combined_reg = loadObject(run_path[0]["CombinedRegistrationPath"])
        ea = Combined_EntropyAssessment_RBG(client_cert, server_url, combined_reg, seed_path, mod_id, vend_id, entropyId, oe_id, certify, single_mod)
        ea.login()
        ea.send_reg()
        responseCount=0
        #for response in ea.responses:
            # TODO
        #    ThreadWrapper.runner_data(server_url, response, conditioned[responseCount], raw_noise[responseCount], restart_test[responseCount], client_cert, rawNoiseSampleSize[responseCount], restartSampleSize[responseCount])
        #    ThreadWrapper.runner_stats(server_url, response, client_cert)
        #    responseCount = responseCount + 1

        exit(0)

    # Certify a previously registered random bit generator
    elif run_type == "certifyrbg":

        # TODO
        print("Using values from previous run..\n")

        client_cert, seed_path, server_url, esv_version = parse_config(config_path)
        assessment_reg, raw_noise, rawNoiseSampleSize, restart_test, restartSampleSize, conditioned, supporting_paths, comments, sdType, mod_id, vend_id, entropyId, oe_id, certify, single_mod, responses, pudEntropyCertificate, pudFilePath, entropyCertificate = parse_run(run_path)

        rbg = RandomBitGenerator(client_cert, server_url, random_bit_generator_reg, seed_path, mod_id, vend_id, entropyId, oe_id, certify, single_mod)
        rbg.responses = responses
        rbg.login()
        
        certSup = sendAllSupportingDocuments(comments, sdType, supporting_paths, server_url, client_cert, ea.auth_header)
        rbg.send_certify(certSup, client_cert, ea.login_jwt, esv_version)
    
        exit(0)

    else:
        print(f"Unable to find run type {run_type}, no actions performed")
        exit(1)

    # Perform actions
    if flags["clear_history"]:
        clear_history()

    if flags["ea_registration"]:
        register_entropy_assessment()

    if flags["supporting_document_upload"]:
        submit_supporting_documentation()

    if flags["ea_certify"]:
        certify_entropy_assessment()

    if flags["update_pud_certify"]:
        certify_update_public_use_document()

    exit(0)
