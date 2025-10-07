import requests
from authentication.login import get_auth_header
from utilities.utils import check_status, pretty_print
import globalenv

# Step 6: Send Certification 
def send_post_certify(cert_supp):
        
    print("\n*** Starting Certification Process")

    # Fill out certify payload
    cert_data = cert_prep(cert_supp)
    
    if globalenv.verboseMode:
        print("Outgoing cert request = ")
        pretty_print(cert_data)

    responseFromCert = requests.request("POST", globalenv.server_url + '/certify', cert=(globalenv.client_cert, globalenv.client_key), headers=get_auth_header(), json=cert_data)
    check_status(responseFromCert)

    return responseFromCert.json()[1]

def send_certify_newOE(self, cert_supp, client_cert, login_jwt, esv_version, certificateID):
        
    if self.certify:
        print("\n*** Starting Update Certification Process")
        auth_header = {'Authorization': 'Bearer ' + login_jwt}
        cert_temp = open('jsons/temp_certify.json', 'w')

        # TODO: Build this automatically 
        cert_temp.write("[{\"esvVersion\": \"1.0\"},{\"entropyId\": \"E123\", \"limitEntropyAssessmentToSingleModule\": false,\"supportingDocumentation\": [],\"entropyAssessments\":[{\"eaId\": null,\"oeId\": null,\"accessToken\": \"<jwt-with-claims-for-eaId1>\"}]}]")

        cert_temp.close()
        cert_temp = open('jsons/temp_certify.json','r')
        cert_file = json.load(cert_temp)
        
        i=0
        ea_ids = []
        entr_jwts = []
        for response in self.responses:
            ea_ids.append(response.ea_id)
            entr_jwts.append(response.entr_jwt)
        cert_json = cert_prep_add_oe(cert_file, cert_supp, esv_version, certificateID, self.single_mod, self.entropy_id, ea_ids, self.oe_id, entr_jwts)

        if globalenv.verboseMode:
            print("Outgoing cert request = ")
            print(cert_json)
        responseFromCert = requests.request("POST", self.server_url + '/certify/AddOE', cert = client_cert, headers=auth_header, json=cert_json)
        check_status(responseFromCert)
        if globalenv.verboseMode:
            print("Response coming back = ")
            print(responseFromCert)
        status, messageList, elementList = utilities.parsing.parse_certify_response(responseFromCert)
        print("\nStatus: " + status + "\n")
        if(len(messageList) > 1):
            print("Message List: ")
            print(*messageList, sep = "\n")
            print("")
        print("Entropy Assessment:")
        for element in elementList:
            print("Location:" + str(element["reference"]))
            for message in element["messageList"]:
                print("   Message:" + message)

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

    for doc in cert_supp.supporting_documentation: #add supporting document IDs and JWTs
        cert_data[1]["supportingDocumentation"].append({"sdId": doc.sd_id, "accessToken": doc.access_token})
    
    return cert_data

def cert_prep_add_oe(certify, certSup, esv_version, certificateID, limitVendor, entropyId, eaIDs, oeIds, entrjwts): 
    
    certify[0]["esvVersion"] = esv_version
    certEntropy = certify[1]["entropyAssessments"] = []
    i = len(eaIDs)
    for x in range(i):
        certEntropy.append({"eaId":int(eaIDs[x]), "oeId":oeIds[x], "accessToken":entrjwts[x]})

    certify[1]["limitEntropyAssessmentToSingleModule"] = limitVendor
    certify[1]["entropyId"] = entropyId #int(eaID) #entropyId
    certify[1]["entropyCertificate"] = certificateID

    for info in reversed(certSup): #add supporting document IDs and JWTs
        certify[1]["supportingDocumentation"].append(info[0])
    
    return certify