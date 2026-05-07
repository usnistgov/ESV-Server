from array import array
import json
import requests
from utilities.utils import add_to_prev_run, get_rbg_ids, cert_prep, log, check_status, cert_prep_add_oe
import time
from totp.totp import generate_pass, login_payload
import globalenv
import utilities.parsing
import response_rbg_class
import entropy_class

class RandomBitGenerator():

    def __init__(self, client_cert, server_url, rbg_reg, seed_path, mod_id, vend_id, rgb_id, oe_id, certify, single_mod): 
        self.client_cert = client_cert
        self.server_url = server_url
        self.rbg_reg = rbg_reg
        self.single_mod = single_mod
        self.mod_id = mod_id
        self.vend_id = vend_id
        self.ergb_id = rgb_id
        self.oe_id = oe_id
        self.seed_path = seed_path
        self.certify = certify      
        self.auth_header = ''
        self.cert_supp = ''

    def parse_response(self,response):
        rbg_id = get_rbg_ids(response)
        entr_jwt = response['accessToken']

        response = response_rbg_class.ResponseRBG(rbg_id, entr_jwt,"")
        add_to_prev_run(response)

        return response

    # Step 1: Login (Adds: login_jwt, Edits: auth_header)
    def login(self):

        print("Logging in...")
        login_jwt, auth_header = entropy_class.EntropyAssessment.jwt_refresh(self.seed_path, self.client_cert, self.server_url)
        self.login_jwt = login_jwt 
        self.auth_header = auth_header
        print("\nLogin Success!")

    # Step 2: Send Registration 
    def send_reg(self):
        print("\n***Sending Random Bit Generator Registration")
        if globalenv.verboseMode:
            print ("Send Registration Outgoing:")
            print (self.assessment_reg)
        response = requests.post(self.server_url + '/rbg', headers=self.auth_header, cert=self.client_cert, json=self.rbg_reg, verify=False)
        if globalenv.verboseMode:
            print ("\n\nSend Registration Incoming:")
            print (response.json())
        check_status(response)

        response = response.json()
        self.responses = []
        parsedResponse = RandomBitGenerator.parse_response(self,response[1])
        self.responses = [parsedResponse]
        
    # Step 6: Send Certification 
    def send_certify(self, cert_supp, client_cert, login_jwt, esv_version):
            
        if self.certify:
            print("\n*** Starting Certification Process")
            auth_header = {'Authorization': 'Bearer ' + login_jwt}

            cert_data = [
                {"esvVersion": "1.0"},
                {
                    "entropyId": "E123",
                    "limitEntropyAssessmentToSingleModule": False,
                    "moduleId": None,
                    "vendorId": None,
                    "supportingDocumentation": [],
                    "entropyAssessments": [
                        {
                            "eaId": None,
                            "oeId": None,
                            "accessToken": "<jwt-with-claims-for-eaId1>"
                        }
                    ]
                }
            ]
            
            i=0
            rbg_ids = []
            entr_jwts = []
            for response in self.responses:
                rbg_ids.append(response.rbg_id)
                entr_jwts.append(response.entr_jwt)
            cert_json = cert_prep(cert_data, cert_supp, esv_version, self.single_mod, self.mod_id, self.vend_id, self.rbg_id, rbg_ids, self.oe_id, entr_jwts)
            if globalenv.verboseMode:
                print("Outgoing cert request = ")
                print(cert_json)
            responseFromCert = requests.request("POST", self.server_url + '/certify/rbg', cert = client_cert, headers=auth_header, json=cert_json)
            check_status(responseFromCert)
            status, messageList, elementList = utilities.parsing.parse_certify_response(responseFromCert)
            if globalenv.verboseMode:
                print("Response coming back = ")
                print(responseFromCert)
            print("\nStatus: " + status + "\n")
            print("Message List: ")
            print(*messageList, sep = "\n")
            print("")
            print("Random Bit Generator:")
            for element in elementList:
                print("Location:" + str(element["reference"]))
                for message in element["messageList"]:
                    print("   Message:" + message)

   
 