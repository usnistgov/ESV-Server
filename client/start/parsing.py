import sys

from requests import Response
from utilities.utils import check_sd_type, log, run_checks
import json
import utilities.esvutil as esvutil
import certifi
import globalenv

#Parse the config file into usable variables
def parse_config(config_path):
    
    try:
        config = open(config_path, 'r')
        config = json.load(config)
        client_cert = (config[0]['CertPath'], config[0]['KeyPath'])
        log("client_cert", client_cert)
        seed_path = config[0]['TOTPPath']
        server_url = config[0]['ServerURL']
        esv_version = config[0]['EsvVersion']
        log("server_url", server_url)
        '''
        singleMod = config[2]['limitEntropyAssessmentToSingleModule']
        modId = None; vendId = None; oeId = None

        certify = config[1]['Certify'] 
        if certify: #Certification requires module and vendor IDs
            try:
                modId = config[1]['moduleID']
                vendId = config[1]['vendorID']
            except:
                print("Error: Module and Vendor IDs are required for certification")
                exit()
        
        if certify and config[2]['numberOfAssessments'] == 1: #Certifying only 1 assessment requires oeID
            try:
                oeId = config[2]['oeID']
            except:
                print("Error: oeID field needed when certifying 1 assessment")
                exit()
'''
        if(globalenv.verboseMode):
            print("Config file successfully parsed")
        return client_cert, seed_path, server_url, esv_version # modId, vendId, oeId, certify, singleMod
    except Exception as e:
        print("There was an error parsing your config file. Please try again")
        print("Error parsing: ", e)

        sys.exit(1)

#Parse the run file into usable variables
def parse_run(run_path):
    try:
        run_file = open(run_path, 'r')
        run_file = json.load(run_file)
        assessment_reg = esvutil.loadObject(run_file[0]["AssessmentRegistrationPath"])
        oeId = []
        rawNoise = []
        restartTest = []
        conditioned = []

        for dataFile in run_file[0]["DataFiles"]:
            oeId.append(dataFile["oeID"])
            rawNoise.append(dataFile["rawNoisePath"])
            restartTest.append(dataFile["restartTestPath"])
            conditioned.append(dataFile["unvettedConditionedPaths"])
        
        numberOfOEs  = assessment_reg[1]['numberOfOEs']
        if len(oeId) != numberOfOEs:
            print("Error: Number of oeIDs provided must match numberOfOEs in Assessment Registration. numberOfOEs is ", numberOfOEs, " but provided number of oeIDs is ", len(oeId))
            sys.exit(1)


        #rawNoise = run_file[0]["DataFiles"]["rawNoisePath"]
        #restartTest = run_file[0]["DataFiles"]["restartTestPath"]
        #conditioned = run_file[0]["DataFiles"]["unvettedConditionedPaths"] #need to take sequence position into account
        
        #supportingDocuments = run_file[0]["SupportingDocuments"]

        supporting_paths = [] # run_file[0]["SupportingDocuments"]["filePaths"]
        comments = [] # run_file[0]["SupportingDocuments"]["comments"]
        sdType = [] # run_file[0]["SupportingDocuments"]["sdType"]
        for supportingDocument in run_file[0]["SupportingDocuments"]:
            supporting_paths.append(supportingDocument["filePath"])
            comments.append(supportingDocument["comment"])
            check_sd_type(supportingDocument["sdType"])
            sdType.append(supportingDocument["sdType"])

        run_checks(comments, sdType, supporting_paths)
        singleMod = run_file[0]["Assessment"]['limitEntropyAssessmentToSingleModule']
        modId = None; vendId = None; #oeId = None

        certify = run_file[0]["Certify"]['Certify'] 
        if certify: #Certification requires module and vendor IDs
            try:
                entropyId = run_file[0]["Certify"]['entropyID']
                modId = run_file[0]["Certify"]['moduleID']
                vendId = run_file[0]["Certify"]['vendorID']
                itar = run_file[0]["Certify"]['itar']

            except:
                print("Error: Entropy, Module and Vendor IDs are required for certification")
                sys.exit(1)
        '''
        if certify and run_file[0]["Assessment"]['numberOfAssessments'] == 1: #Certifying only 1 assessment requires oeID
            try:
                oeId = run_file[0]["Assessment"]['oeID']
            except:
                print("Error: oeID field needed when certifying 1 assessment")
                sys.exit(1)
            numberOfOEs  = assessment_reg[1]['numberOfOEs']
            if len(oeId) != numberOfOEs:
                print("Error: Number of oeIDs provided must match numberOfOEs in Assessment Registration. numberOfOEs is ", numberOfOEs, " but provided number of oeIDs is ", len(oeId))
                sys.exit(1)
                '''
        responseList = []
        if "PreviousRun" in run_file[0]:
            if(globalenv.verboseMode):
                print('PreviousRun detected')
            for eachRun in run_file[0]["PreviousRun"]:
                res = Response()
                res.entr_jwt = eachRun["entr_jwt"]
                res.df_ids = eachRun["df_ids"]
                res.ea_id = eachRun["ea_id"]
                # The supporting document info only goes in the first item in PreviousRun. No need to add it
                # to others because the info is the same
                if "cert_supp" in run_file[0]["PreviousRun"][0]:
                    res.cert_supp = run_file[0]["PreviousRun"][0]["cert_supp"]
                else:
                    res.cert_supp = ""
                responseList.append(res)
            if(globalenv.verboseMode):
                print('PreviousRun parsed')
        else:
            entr_jwt = ""
            df_ids = ""
            ea_id = ""
            cert_supp = ""
            if(globalenv.verboseMode):
                print('No PreviousRun detected')

        if(globalenv.verboseMode):
            print('Run file successfully parsed')
        return assessment_reg, rawNoise, restartTest, conditioned, supporting_paths, comments, sdType, modId, vendId, entropyId, oeId, certify, singleMod, responseList, itar

    except Exception as e:
        print("There was an error parsing your run file. Please try again")
        print("Error parsing: ", e)
        sys.exit(1)

def parse_certify_response(response):
    response = response.json()
    status = response[1]['status']
    messageList = response[1]["information"]["messageList"]
    elementList = response[1]["information"]["entropyAssessmentsReferences"]["elementList"]
    return status, messageList, elementList