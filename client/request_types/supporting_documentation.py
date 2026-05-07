import os
import requests
from authentication.login import get_auth_header
import globalenv
from models.supporting_document import Supporting_Document
from utilities.utils import check_status


def send_post_supp_doc(supporting_document):

    sd_type = supporting_document["sdType"]
    supporting_path = supporting_document["filePath"]
    
    comment = ""
    if "comment" in supporting_document:
        comment = supporting_document["comment"]

    # Prepare upload and payload
    supp_name = os.path.basename(supporting_path)
    files = [('sdFile', (supp_name, open(supporting_path,'rb'),'application/pdf'))]
    payload = {'sdType': sd_type,'sdComments': comment}
    
    # POST
    response = requests.request("POST", globalenv.server_url + '/supportingDocumentation', cert=(globalenv.client_cert, globalenv.client_key), headers=get_auth_header(), data=payload, files=files)
    check_status(response)
    
    response_body = response.json()[1]
    status = response_body['status']

    # Get returnable properties
    if status != "success":
        print(status)
        return 0, ""

    else:
        sd_id = response_body['sdId']
        access_token = response_body['accessToken']

        print(f"{sd_type}: {str(sd_id)} - {supp_name} | Status: {status}")

        return Supporting_Document(sd_id, sd_type, access_token)

def send_all_supp_doc(supporting_documents):

    results = []
    for supporting_document in supporting_documents:
        if "sdType" not in supporting_document:
            print("Error sdType not found in a supporting document")
            exit(1)

        if "filePath" not in supporting_document:
            print("Error filePath not found in a supporting document")
            exit(1)

        results.append(send_post_supp_doc(supporting_document))

    return results

def send_post_update_pud(entropyCertificate, entropyID, sd_id, access_token):

    payload = [
        {
            'esvVersion': globalenv.esv_version
        }, 
        {
            'entropyCertificate': entropyCertificate,
            'entropyId': entropyID,
            'supportingDocument': {'sdId': sd_id, 'accessToken': access_token}
        }
    ]
                                       
    response = requests.request("POST", globalenv.server_url + "/certify/updatePUD", cert=(globalenv.client_cert, globalenv.client_key), headers=get_auth_header(), json=payload)
    check_status(response)

    response_body = response.json()[1]
    status = response_body['status']

    # Note that this endpoint uses "received", not "success" as positive result
    if status != "received":
        print(status)
    else:
        print("Updated Public Use Document successfully received by server")  
