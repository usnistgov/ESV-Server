import requests
from authentication.login import get_auth_header
from models.random_bit_generator import Random_Bit_Generator
from utilities.utils import check_status, pretty_print
import globalenv

def send_post_random_bit_generator(assessment_reg):

    print("\n***Sending Random Bit Generator Registration")

    # This gets wrapped in an rbg object in JSON
    payload = [{"esvVersion": globalenv.esv_version},{"rbg": assessment_reg}]

    if globalenv.verboseMode:
        print("RBG Registration Outgoing:")
        pretty_print(payload)
    
    full_response = requests.post(globalenv.server_url + '/rbgs', headers=get_auth_header(), cert=(globalenv.client_cert, globalenv.client_key), json=payload, verify=False)
    check_status(full_response)
    json_response = full_response.json()[1]     # Get rid of version object

    if globalenv.verboseMode:
        print("\n\nRBG Registration Response:")
        pretty_print(json_response)

    # Response is an array of RBGs even if only one is present
    return Random_Bit_Generator(rbg_id=json_response["url"].split("/")[-1], access_token=json_response["accessToken"])

def send_get_random_bit_generator(rbg):
    full_response = requests.get(globalenv.server_url + '/rbgs/' + str(rbg.rbg_id), headers=get_auth_header(rbg.access_token), cert=(globalenv.client_cert, globalenv.client_key))
    check_status(full_response)
    json_response = full_response.json()[1]
    
    return json_response
    # Print logic moved to calling function to avoid printing retry:30 over and over
