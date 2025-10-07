from authentication.login import get_auth_header
import globalenv
from utilities.utils import check_data_file_size, check_status
import requests
import os
import time

def send_get_data_file_status(ea_id, id, jwt):

    status = ""
    terminal_states = ['error', 'runsuccessful'] 

    # Loop on statuses until a terminal state is reached
    while not any (x in status.lower() for x in terminal_states):
        response = requests.get(globalenv.server_url + '/entropyAssessments/' + str(ea_id) + '/dataFiles/' + str(id), headers=get_auth_header(jwt), cert=(globalenv.client_cert, globalenv.client_key))
        try:
            status = str(response.json()[1]['status'])
            print("id: " + str(response.json()[1]['id']) + " | status: " + status)
        except:
            print("Error checking ID " + str(id))
            responseJson = response.json()
            errorMsg = responseJson[1]["error"]
            print(errorMsg)
            exit(1)

        # If a terminal status is not found, sleep for 15 seconds and repeat
        if not any (x in status.lower() for x in terminal_states): 
            time.sleep(15)

    return response

def send_post_data_file(ea_id, df_id, file_path, jwt, bits_per_sample = 0):

    # Check file is valid
    check_data_file_size(file_path)

    # Add in data file-specific bits per sample
    payload = {}
    if bits_per_sample is not 0:
        payload["dataFileSampleSize"] = bits_per_sample

    # Build payload and submit
    files = [("dataFile", (os.path.basename(file_path), open(file_path, "rb"), "application/octet-stream"))]
    response = requests.post(globalenv.server_url + '/entropyAssessments/' + str(ea_id) + "/dataFiles/" + str(df_id), headers=get_auth_header(jwt), cert=(globalenv.client_cert, globalenv.client_key), data=payload, files=files)
    check_status(response)

    return response

