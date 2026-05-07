import requests
from authentication.login import get_auth_header
from utilities.utils import check_status, pretty_print
import globalenv

def send_post_certify(cert_supp):
        
    print("\n*** Starting Entropy Certification Process")

    # Fill out certify payload
    cert_data = cert_prep(cert_supp)
    
    if globalenv.verboseMode:
        print("Outgoing cert request = ")
        pretty_print(cert_data)

    responseFromCert = requests.request("POST", globalenv.server_url + '/certify', cert=(globalenv.client_cert, globalenv.client_key), headers=get_auth_header(), json=cert_data)
    check_status(responseFromCert)

    return responseFromCert.json()[1]

def send_post_certify_add_oe(cert_supp):
        
    print("\n*** Starting AddOE Certification Process")

    # Fill out certify payload
    cert_data = cert_prep_add_oe(cert_supp)
    
    if globalenv.verboseMode:
        print("Outgoing cert request = ")
        pretty_print(cert_data)

    responseFromCert = requests.request("POST", globalenv.server_url + '/certify/addOE', cert=(globalenv.client_cert, globalenv.client_key), headers=get_auth_header(), json=cert_data)
    check_status(responseFromCert)

    return responseFromCert.json()[1]

def send_post_certify_rbg(cert_supp):
        
    print("\n*** Starting RBG Certification Process")

    # Fill out certify payload
    cert_data = cert_prep_rbg(cert_supp)
    
    if globalenv.verboseMode:
        print("Outgoing cert request = ")
        pretty_print(cert_data)

    responseFromCert = requests.request("POST", globalenv.server_url + '/certify/rbg', cert=(globalenv.client_cert, globalenv.client_key), headers=get_auth_header(), json=cert_data)
    check_status(responseFromCert)

    return responseFromCert.json()[1]

def cert_prep(cert_supp): 

    cert_data = [
        {"esvVersion": globalenv.esv_version},
        {
            "entropyId": cert_supp.entropy_id,
            "limitEntropyAssessmentToSingleModule": True,       # Defaulting to true for now
            "moduleId": cert_supp.module_id,
            "vendorId": cert_supp.vendor_id,
            "supportingDocumentation": [],
            "entropyAssessments": []
        }
    ]

    for ea in cert_supp.entropy_assessments:
        cert_data[1]["entropyAssessments"].append({"eaId": ea.ea_id, "oeId": ea.oe_id, "accessToken": ea.access_token})

    for doc in cert_supp.supporting_documentation:
        cert_data[1]["supportingDocumentation"].append({"sdId": doc.sd_id, "accessToken": doc.access_token})
    
    return cert_data

def cert_prep_add_oe(cert_supp): 
    
    cert_data = [
        {"esvVersion": globalenv.esv_version},
        {
            "entropyId": cert_supp.entropy_id,
            "limitEntropyAssessmentToSingleModule": True,       # Defaulting to true for now
            "entropyCertificate": cert_supp.entropy_certificate,
            "supportingDocumentation": [],
            "entropyAssessments": []
        }
    ]

    for ea in cert_supp.entropy_assessments:
        cert_data[1]["entropyAssessments"].append({"eaId": ea.ea_id, "oeId": ea.oe_id, "accessToken": ea.access_token})

    for doc in cert_supp.supporting_documentation: 
        cert_data[1]["supportingDocumentation"].append({"sdId": doc.sd_id, "accessToken": doc.access_token})
    
    return cert_data

def cert_prep_rbg(cert_supp): 

    cert_data = [
        {"esvVersion": globalenv.esv_version},
        {
            "entropyId": cert_supp.entropy_id,
            "limitEntropyAssessmentToSingleModule": True,       # Defaulting to true for now
            "moduleId": cert_supp.module_id,
            "vendorId": cert_supp.vendor_id,
            "supportingDocumentation": [],
            "rbg": { "rbgId": cert_supp.rbg.rbg_id, "accessToken": cert_supp.rbg.access_token }
        }
    ]

    for doc in cert_supp.supporting_documentation:
        cert_data[1]["supportingDocumentation"].append({"sdId": doc.sd_id, "accessToken": doc.access_token})
    
    return cert_data
