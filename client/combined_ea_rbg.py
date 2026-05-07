import requests
from utilities.utils import add_to_prev_run, get_ids, check_status
import globalenv
import response_class
import entropy_class

class Combined_EntropyAssessment_RBG():

    def __init__(self, client_cert, server_url, combined_reg, seed_path, mod_id, vend_id, entropy_id, oe_id, certify, single_mod): #, rawNoise, restartTest, conditioned, supporting_paths, comments):
        self.client_cert = client_cert
        self.server_url = server_url
        self.combined_reg = combined_reg
        self.single_mod = single_mod
        self.mod_id = mod_id
        self.vend_id = vend_id
        self.entropy_id = entropy_id
        self.oe_id = oe_id
        self.seed_path = seed_path
        self.certify = certify      
        self.auth_header = ''
        self.cert_supp = ''

    def parse_response(self,response):
        ea_id, rbg_ids = get_ids(response)
        entr_jwt = response['accessToken']

        response = response_class.Response(ea_id, rbg_ids, entr_jwt,"")
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
        print("\n***Sending Combined Entropy Assessment / Random Bit Generator Registration")
        if globalenv.verboseMode:
            print ("Send Registration Outgoing:")
            print (self.assessment_reg)
        response = requests.post(self.server_url + '/combined', headers=self.auth_header, cert=self.client_cert, json=self.assessment_reg, verify=False)
        if globalenv.verboseMode:
            print ("\n\nSend Registration Incoming:")
            print (response.json())
        check_status(response)

        response = response.json()
        self.responses = []
        if not(isinstance(response[1], list)):
            # is one response
            if globalenv.verboseMode:
                print("Number of Entropy Assessments: 1")
               
            parsedResponse = entropy_class.EntropyAssessment.parse_response(self,response[1])
            self.responses = [parsedResponse]
        else:
            # multiple OEs
            if globalenv.verboseMode:
                print("Number of Entropy Assessments: " + str(len(response[1])))
            for oneEA in response[1]: 
                parsedResponse = entropy_class.EntropyAssessment.parse_response(self,oneEA)
                self.responses.append(parsedResponse)
    # TODO: Parse RBG

