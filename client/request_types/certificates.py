import requests
from authentication.login import get_auth_header
import globalenv
from utilities.utils import check_status, pretty_print


def send_get_entropy_certificate(certificateID):

    response = requests.request("GET", globalenv.server_url + "/entropyCertificate/" + certificateID, cert=(globalenv.client_cert, globalenv.client_key), headers=get_auth_header())
    check_status(response)

    json_response = response.json()[1]

    # Display certificate
    if globalenv.verboseMode:
        print("Raw response:\n")
        pretty_print(json_response)
    else:
        try:
            print("Certificate Information:\n")
            print("Certificate ID: " + str(json_response["certificateId"]))
            print("Certificate Number: " + str(json_response["certificateNumber"]))
            print("Description: " + str(json_response["description"]))
            print("Physical: " + str(json_response["isPhysical"]))
            print("Reusable: " + str(json_response["isReusable"]))

        except KeyError as e:
            print(f"Error: Missing key '{e}' in certificate.")
        except Exception as e:
            print(f"Error: An error occurred while parsing certificate: {e}")
