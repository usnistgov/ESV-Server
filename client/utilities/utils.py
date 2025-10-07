import json
import requests
import requests
import globalenv
import os.path

from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Valid supporting documentation types
VALID_SD_TYPES = ["EntropyAssessmentReport", "PublicUseDocument", "DataCollectionAttestation", "RBGReport", "Other"]

# Files must be exactly 1 million bytes
VALID_FILE_SIZE = 1000000

def add_version_object(json_object):
    return [{"esvVersion": globalenv.esv_version},json_object]

def pretty_print(json_object):
    print(json.dumps(json_object, indent=4) + "\n")

# Checks the status code of a response and exits with a 1 if error is 400s or 500s and prints error message        
def check_status(response):
    if int(response.status_code) / 100 >= 4:
        try:
            print("Error: Status code " + str(response.status_code))
            try:
                print(response.json())
            except:
                if globalenv.verboseMode:
                    print(response.content)    
            if int(response.status_code) == 403 and "TOTP" not in str(response.content):
               print("Access denied error.  Verify certificate is valid and accepted by server.")
            exit(1)
        except:
            exit(1)

def check_data_file_size(filepath):
    filesize = os.path.getsize(filepath)
    if filesize != VALID_FILE_SIZE:
        print(f"Error: '{filepath}' is ({str(filesize)} bytes). Required size is {str(VALID_FILE_SIZE)} bytes.")
        exit(1)
    