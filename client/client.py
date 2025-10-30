from authentication.login import login
from client_actions import certify_combined_rbg_ea, certify_entropy_assessment, certify_entropy_assessment_add_oe, certify_random_bit_generator, certify_update_public_use_document, clear_history, display_data_file_status, display_entropy_certificate, get_random_bit_generator, refresh_tokens, register_entropy_assessment, register_random_bit_generator, submit_supporting_documentation
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
    return [response for response in responses if response[0] == socket.AF_INET]
socket.getaddrinfo = new_getaddrinfo

if __name__ == "__main__":

    #run is required, but config_path and run_path are not needed when doing runs 2 or 5
    #Therefore, config_path and run_path have -- prefixes
    parser = argparse.ArgumentParser()
    parser.add_argument('run', default="full", help="Choose a run type:\
                    \n- (full) Full run of an initial entropy source submission\
                    \n- (fullAddOE) Full run to add an OE to an existing entropy source certificate\
                    \n- (status) Check Data File Progress (of last run)\
                    \n- (submit) Submit Entropy Assessment and Data Files, does not certify\
                    \n- (support) Upload Supporting Documentation\
                    \n- (submitRBG) Submit Random Bit Generator\
                    \n- (fulltRBG_EA) Submit and certify both an Entropy Assessment and Random Bit Generator\
                    \n- (fullRBG) Submit and certify a Random Bit Generator\
                    \n- (certify) Certify an Entropy Assessment (Uses IDs from history)\
                    \n- (certifyRBG) Certify an RBG (Uses IDs from history)\
                    \n- (certifyAddOE) Add new OE to existing entropy source certificate)\
                    \n- (getCertificate) Get completed entropy source or random bit generator certificate (needs certificateId, does not need a --run_path)\
                    \n- (updatePUD) Update the PUD for an already certified entropy source\
                    \n- (refresh) Refreshes all tokens in a run file\n\n")
    
    # TODO add option to refresh all access tokens in a run file

    parser.add_argument('--stats_90B_path', default="", help= "Output file for 90B statistical results json")
    parser.add_argument('--config_path', help="Input the path to your configuration json")
    parser.add_argument('--run_path', help= "Input the path to your run json")
    parser.add_argument("-v", "--verbose", action="store_true", help="Run in 'verbose' mode")
    parser.add_argument('--certificateId', help="The number of the certificate requested")
    args = parser.parse_args()

    # Determine actions based on run type
    run_type = args.run.lower()

    # Set up globals based on command line arguments
    globalenv.verboseMode = args.verbose
    
    if args.stats_90B_path == "":
        globalenv.record_90B_stats = False
    else:
        globalenv.record_90B_stats = True
        globalenv.stats_90B_path = args.stats_90B_path

    # Don't need a run file to get a certificate
    if run_type != "getcertificate":
        globalenv.run_path = args.run_path
        parse_run(args.run_path)        # Sets globalenv.run_data
    
    parse_config(args.config_path)  # Sets globalenv config properties

    # Perform a login
    login()

    # Perform actions
    # if run_type == "run type":
    #   actions should begin with either `clear_history()` or `refresh_tokens()`.
    #   `clear_history()` will ensure that the history object is empty (it won't erase it if it exists)
    #       so the following commands can write to the history.
    #   `refresh_tokens()` will refresh all tokens in the run file to be used by subsequent actions.
    #   
    #   Actions that rely on others to complete, i.e. a certify requests requires the submitted data files to complete testing
    #       will retry infinitely on the status check until a terminal status is obtained (could still be an error).
    #
    #   Users may define their own actions stitching together already-defined functions as needed.

    if run_type == "full":              # A complete entropy source submission
        clear_history()
        register_entropy_assessment()
        submit_supporting_documentation()
        display_data_file_status(retry=True)
        certify_entropy_assessment()

    elif run_type == "submit":          # Register an entropy source and upload data files
        clear_history()
        register_entropy_assessment()
    
    elif run_type == "support":         # Upload supporting documentation
        submit_supporting_documentation()

    elif run_type == "certify":         # Certify a previously registered entropy source
        refresh_tokens()
        display_data_file_status(retry=True)
        certify_entropy_assessment()

    elif run_type == "fulladdoe":       # Register and add an OE to an existing entropy source certificate
        clear_history()
        register_entropy_assessment()
        submit_supporting_documentation()
        display_data_file_status(retry=True)
        certify_entropy_assessment_add_oe()

    elif run_type == "certifyaddoe":    # Add an OE to an existing entropy source certificate
        refresh_tokens()
        display_data_file_status(retry=True)
        certify_entropy_assessment_add_oe()

    elif run_type == "updatepud":       # Update the Public Use Document on an existing entropy source certificate
        clear_history()
        submit_supporting_documentation()
        certify_update_public_use_document()

    elif run_type == "status":          # Check the status of previously submitted data files
        refresh_tokens()
        display_data_file_status(retry=True)

    elif run_type == "getcertificate":  # View an entropy source certificate
        display_entropy_certificate(args.certificateId)

    elif run_type == "refresh":         # Refresh all tokens in a run file
        refresh_tokens()

    elif run_type == "submitrbg":       # Register a random bit generator
        clear_history()
        register_random_bit_generator()

    elif run_type == "fullrbg":         # Register and certify a random bit generator
        clear_history()
        register_random_bit_generator()
        submit_supporting_documentation()
        get_random_bit_generator(retry=True)
        certify_random_bit_generator()

    elif run_type == "fullrbg_ea":    # Register and certify a random bit generator and entropy source with data files
        clear_history()
        register_entropy_assessment()
        register_random_bit_generator()
        submit_supporting_documentation()
        display_data_file_status(retry=True)
        get_random_bit_generator(retry=True)
        certify_combined_rbg_ea()
    
    elif run_type == "certifyrbg":    # Certify a previously registered random bit generator
        refresh_tokens()
        get_random_bit_generator(retry=True)
        certify_random_bit_generator()

    else:
        print(f"Unable to find run type {run_type}, no actions performed")
        exit(1)

    exit(0)
