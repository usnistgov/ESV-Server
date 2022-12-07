from array import array
import json
import requests
from utilities.utils import add_to_prev_run, get_ids, cert_prep, log, check_status
import time
from totp.totp import generate_pass, login_payload
import globalenv
import start.parsing
import response_class

class EntropyAssessment():

    def __init__(self, client_cert, server_url, assessment_reg, seed_path, mod_id, vend_id, entropy_id, oe_id, certify, single_mod, itar): #, rawNoise, restartTest, conditioned, supporting_paths, comments):
        self.client_cert = client_cert
        self.server_url = server_url
        self.assessment_reg = assessment_reg
        self.single_mod = single_mod
        self.mod_id = mod_id
        self.vend_id = vend_id
        self.entropy_id = entropy_id
        self.oe_id = oe_id
        self.seed_path = seed_path
        self.certify = certify
        # Changed 9/14/2022 because itar is now set in certify not registration
        #self.itar = assessment_reg[1]['itar']
        self.itar = itar        
        self.auth_header = ''
        self.cert_supp = ''

    def parse_response(self,response):
        ea_id, df_ids = get_ids(response)
        entr_jwt = response['accessToken']
    
        #log("entr_jwt", entr_jwt)
        #log("df_ids", df_ids)
        #log("ea_id", ea_id)

        response = response_class.Response(ea_id, df_ids, entr_jwt,"")
        add_to_prev_run(response)

        return response

    # Step 1: Login (Adds: login_jwt, Edits: auth_header)
    def login(self):

        print("Logging in...")
        login_jwt, auth_header = EntropyAssessment.jwt_refresh(self.seed_path, self.client_cert, self.server_url)
        self.login_jwt = login_jwt 
        self.auth_header = auth_header
        print("\nLogin Success!")

    # Step 2: Send Registration (Adds: ea_id, df_ids, entr_jwt)
    def send_reg(self):
        print("\n***Sending Entropy Assessment Registration")
        if globalenv.verboseMode:
            print ("Send Registration Outgoing:")
            print (self.assessment_reg)
        response = requests.post(self.server_url + '/entropyAssessments', headers=self.auth_header, cert=self.client_cert, json=self.assessment_reg, verify=False)
        if globalenv.verboseMode:
            print ("\n\nSend Registration Incoming:")
            print (response.json())
        check_status(response)
        # print("Sent.")

        response = response.json()
        self.responses = []
        if not(isinstance(response[1], list)):
            # is one response
            if globalenv.verboseMode:
                print("Number of Entropy Assessments: 1")
               
            parsedResponse = EntropyAssessment.parse_response(self,response[1])
            self.responses = [parsedResponse]
            #self.ea_id, self.df_ids, self.entr_jwt = EntropyAssessment.parse_response(self,response[1])

        else:
            # multiple OEs
            if globalenv.verboseMode:
                print("Number of Entropy Assessments: " + str(len(response[1])))
                for oneEA in response[1]:
                    
                    parsedResponse = EntropyAssessment.parse_response(self,oneEA)
                    self.responses.append(parsedResponse)
                    #self.ea_id, self.df_ids, self.entr_jwt = EntropyAssessment.parse_response(self,oneEA)

            
    
    # Step 6: Send Certification 
    def send_certify(self, cert_supp, client_cert, login_jwt, esv_version):
            
        if self.certify:
            i=0
            for response in self.responses:
                print("\n*** Starting Certification Process")
                auth_header = {'Authorization': 'Bearer ' + login_jwt}

                cert_temp = open('jsons/temp_certify.json', 'w')

                # TODO: Build this automatically 
                cert_temp.write("[{\"esvVersion\": \"1.0\"},{\"entropyId\": \"E123\", \"limitEntropyAssessmentToSingleModule\": false,\"moduleId\": null,\"vendorId\": null,\"supportingDocumentation\": [],\"entropyAssessments\":[{\"eaId\": null,\"oeId\": null,\"accessToken\": \"<jwt-with-claims-for-eaId1>\"}]}]")
                #cert_temp.write("[{\"esvVersion\": \"1.0\"},{\"itar\": false,\"limitEntropyAssessmentToSingleModule\": false,\"moduleId\": null,\"vendorId\": null,\"supportingDocumentation\": [],\"entropyAssessments\":[{\"entropyId\": null,\"oeId\": null,\"accessToken\": \"<jwt-with-claims-for-eaId1>\"}]}]")

                cert_temp.close()
                cert_temp = open('jsons/temp_certify.json','r')
                cert_file = json.load(cert_temp)
                #import os; os.remove('jsons/temp_certify.json')
            
                cert_json = cert_prep(cert_file, cert_supp, esv_version, self.single_mod, self.mod_id, self.vend_id, self.entropy_id, response.ea_id, self.oe_id[i], response.entr_jwt, self.itar)
                if globalenv.verboseMode:
                    print("Outgoing cert request = ")
                    print(cert_json)
                responseFromCert = requests.request("POST", self.server_url + '/certify', cert = client_cert, headers=auth_header, json=cert_json)
                check_status(responseFromCert)
                status, messageList, elementList = start.parsing.parse_certify_response(responseFromCert)

                print("\nStatus: " + status + "\n")
                print("Message List: ")
                print(*messageList, sep = "\n")
                print("")
                print("Entropy Assessment:")
                #print(*elementList, sep = "\n")
                for element in elementList:
                    print("Location:" + str(element["location"]))
                    for message in element["messageList"]:
                        print("   Message:" + message)
                i+=1
            #print(json.dumps(response.json(), indent=4, sort_keys = True))

    # Used for login
    def jwt_refresh(seed_path, client_cert, server_url):

        payload = login_payload(generate_pass(seed_path))
        if globalenv.verboseMode:
            print ("JWT Refresh Outgoing:")
            print (payload)
        
        response = requests.post(server_url + '/login', cert=client_cert, json=payload)
        if globalenv.verboseMode:
            print ("JWT Refresh Incoming:")
            print (response)
        check_status(response)     
        jwt_token = response.json()[1]['accessToken']
        auth_header = {'Authorization': 'Bearer ' + jwt_token}

        return jwt_token, auth_header

