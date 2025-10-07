import time
import requests
from authentication.totp import did_totp_fail, generate_pass, get_current_window
import globalenv
from utilities.utils import check_status, pretty_print

def login():
    print("Logging in...\n")
    login_jwt = get_jwt()
    globalenv.jwt = login_jwt 
    print("Login Success!\n")

def get_auth_header(jwt=""):
    if jwt == "":
        return {'Authorization': 'Bearer ' + globalenv.jwt}
    else:
        return {'Authorization': 'Bearer ' + jwt}

# Checks TOTP window and refresh jwt if not in previous window 
def refresh_jwt(ea_jwt, sec = get_current_window() - 1):
    
    # if in same window, keep same token
    if sec == get_current_window(): 
        if globalenv.verboseMode:
            print("Same TOTP window, using previous token")
        return ea_jwt
    
    # try refresh
    try: 
        if globalenv.verboseMode:
            print("New TOTP window, renewing previous token")
        totpCheck = True
        response = ""
        while(totpCheck):
            payload = refresh_payload(generate_pass(globalenv.seed_path), ea_jwt)
            response = requests.post(globalenv.server_url + '/login', cert=(globalenv.client_cert, globalenv.client_key), json=payload, verify=False)
            
            if globalenv.verboseMode:
                print(response.json())

            if did_totp_fail(response):
                totpCheck = True
                print("TOTP Window has already been used. Will retry in 30 seconds...")
                time.sleep(30)
            else:
                totpCheck = False
                
        return response.json()[1]['accessToken']
    except Exception as e:
        print(e)
        exit(1)

# Used for login
def get_jwt():

    payload = login_payload(generate_pass(globalenv.seed_path))
    if globalenv.verboseMode:
        print("JWT Refresh Outgoing:")
        pretty_print(payload)

    try:
        response = requests.post(globalenv.server_url + '/login', cert=(globalenv.client_cert, globalenv.client_key), json=payload)
    except requests.exceptions.SSLError as e:
        print("SSL Error:", e)
        print("Verify certificate is valid and accepted by server.")
        exit(1)

    check_status(response)
    if globalenv.verboseMode:
        print("JWT Refresh Incoming:")
        pretty_print(response.json()[1])

    return response.json()[1]['accessToken']

# Generates payload for JWT refresh
def refresh_payload(passw, jwt):

    return [
        {'esvVersion': globalenv.esv_version},
        {'password': passw, 'accessToken': jwt}
    ]

# Generates payload for login
def login_payload(passw):

    return [
        {'esvVersion': globalenv.esv_version},
        {'password': passw}
    ]
