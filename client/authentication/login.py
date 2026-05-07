import time
import requests
from authentication.totp import generate_pass
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

def did_totp_fail(response):
    if int(response.status_code) != 403:
        return False
    
    responseJson = response.json()
    errorMsg = responseJson[1]["error"]

    if "TOTP Window has already been used" in errorMsg:
        return True
    
    return False

# Checks TOTP window and refresh jwt if not in previous window 
def refresh_jwt(jwts):
    
    try: 
        totpCheck = True
        response = ""
        while(totpCheck):
            payload = refresh_payload(generate_pass(globalenv.seed_path), jwts)
            response = requests.post(globalenv.server_url + '/login/refresh', cert=(globalenv.client_cert, globalenv.client_key), json=payload)

            if did_totp_fail(response):
                totpCheck = True
                print("TOTP Window has already been used. Will retry automatically in 10 seconds...")
                time.sleep(10)
            else:
                totpCheck = False
                
        return response.json()[1]['accessToken']
    except requests.exceptions.SSLError as e:
        print("SSL Error:", e)
        print("Verify certificate is valid and accepted by server.")
        exit(1)
    except Exception as e:
        print(e)
        exit(1)

# Used for login
def get_jwt():

    payload = login_payload(generate_pass(globalenv.seed_path))
    if globalenv.verboseMode:
        print("JWT Login Outgoing:")
        pretty_print(payload)

    try:
        response = requests.post(globalenv.server_url + '/login', cert=(globalenv.client_cert, globalenv.client_key), json=payload)
    except requests.exceptions.SSLError as e:
        print("SSL Error:", e)
        print("Verify certificate is valid and accepted by server.")
        exit(1)

    check_status(response)
    if globalenv.verboseMode:
        print("JWT Login Incoming:")
        pretty_print(response.json()[1])

    return response.json()[1]['accessToken']

# Generates payload for JWT refresh
def refresh_payload(passw, jwt):
    return [{'esvVersion': globalenv.esv_version},{'password': passw, 'accessToken': jwt}]

# Generates payload for login
def login_payload(passw):
    return [{'esvVersion': globalenv.esv_version},{'password': passw}]
