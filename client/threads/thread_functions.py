from utilities.utils import check_status
import requests
import threading
import os
import time
import sys
import json

#thread-safe printing
def safe_print(*args, sep=" ", end="", **kwargs):
    joined_string = sep.join([ str(arg) for arg in args ])
    print(joined_string  + "\n", sep=sep, end=end, **kwargs)  

#multithreading version of getting data files
def get_status(server_url, ea_id, id, entrjwt, client_cert):
    
    datafileUrl = server_url + '/entropyAssessments/' + ea_id + '/dataFiles/'
    auth_header = {'Authorization': 'Bearer ' + entrjwt}
    dataFiles = []; dataLabels = []; statLabels = []; stats = []
    status = ""
    substrings = ['error', 'runsuccessful'] 

    while not any (x in status.lower() for x in substrings): #check for a certain value in status
        response = requests.get(datafileUrl + id, headers = auth_header, cert=client_cert)
        #print("Raw status")
        #print(response.json())
        try:
            status = str(response.json()[1]['status'])
            safe_print("id: " + str(response.json()[1]['id']) + " | status: " + response.json()[1]['status'])
        except:
            safe_print("Error checking ID " + str(id))
            #safe_print(response.json())
            responseJson = response.json()
            errorMsg = responseJson[1]["error"]
            safe_print(errorMsg)
            #break
            sys.exit(1)
        if not any (x in status.lower() for x in substrings): 
            time.sleep(15)

    return response
    

#Step 3: Submit data files (conditioning, threading)
def df_upload_cond(server_url, ea_id, df_ids, jwt, i, conditioned, client_cert):
    url = server_url + "/entropyAssessments/" + ea_id + "/dataFiles/" 
    auth_header = {'Authorization': 'Bearer ' + jwt}
    payload = {}
    
    files=[('dataFile',(os.path.basename(conditioned[i]),open(conditioned[i],'rb'),'application/octet-stream'))]
    response = requests.request("POST", url + df_ids[i + 2], cert = client_cert, headers=auth_header, data = payload, files=files)
    check_status(response)
    return response

#Submit data files (raw, threading)
def df_upload_raw(server_url, ea_id, df_ids, jwt, raw_noise, client_cert, sampleSize):
    url = server_url + "/entropyAssessments/" + ea_id + "/dataFiles/" 
    auth_header = {'Authorization': 'Bearer ' + jwt}
    payload = {}

    #Send rawNoise
    if(sampleSize != -1):
        files= { 
            'dataFile': (os.path.basename(raw_noise),open(raw_noise,'rb'),'application/octet-stream'),
            'DataFileSampleSize': sampleSize }
    else:
        files=[('dataFile',(os.path.basename(raw_noise),open(raw_noise,'rb'),'application/octet-stream'))]
    
 
    response = requests.request("POST", url + df_ids[0], cert = client_cert, headers=auth_header, data = payload, files=files)
    
    check_status(response)
    return response

#Submit data files (restart, threading)
def df_upload_restart(server_url, ea_id, df_ids, jwt, restart_test, client_cert, sampleSize):
    url = server_url + "/entropyAssessments/" + ea_id + "/dataFiles/" 
    auth_header = {'Authorization': 'Bearer ' + jwt}
    payload = {}
    
    #Send restartTest
    if(sampleSize != -1):
        files= { 
            'dataFile': (os.path.basename(restart_test),open(restart_test,'rb'),'application/octet-stream'),
            'DataFileSampleSize': sampleSize }
    else:
        files=[('dataFile',(os.path.basename(restart_test),open(restart_test,'rb'),'application/octet-stream'))]
    
    response = requests.request("POST", url + df_ids[1], cert = client_cert, headers=auth_header, data = payload, files=files)
    check_status(response)
    return response

#Step 5(2): Send Supporting Documents
def send_supp(comments, sdType, supporting_path, server_url, client_cert, auth_header):
    cert_supp = []
    supp_name = os.path.basename(supporting_path)
    files=[('sdFile', (supp_name, open(supporting_path,'rb'),'application/pdf'))]
    payload={'sdType': sdType,'sdComments': comments}
    response = requests.request("POST", server_url + '/supportingDocumentation', cert = client_cert, headers=auth_header, data = payload, files=files)
    check_status(response)
    response_1 = response.json()[1]
    status = response_1['status']
    if(status != "success"):
        print (status)
    else:
        sd_id = response_1['sdId']
        print(supp_name + ": " + str(sd_id) + " | Status: " + str(response_1['status']))
        cert_supp.append({"sdId" : sd_id, "accessToken": response_1["accessToken"]})    
    return cert_supp, response

#Step X: Send Updated Public Use Document
def send_updatedPud(previousCertSup, entropyCertificate, entropyID, pud_path, server_url, client_cert, auth_header):

    previousCertSupJson = json.dumps(previousCertSup[0][0])
    previousCertSupJson = json.loads(previousCertSupJson)
    
    cert_supp = []
    pud_name = os.path.basename(pud_path)

    payload = [ {'esvVersion': '1.0'}, {'entropyCertificate': entropyCertificate,
                                        'entropyId': entropyID,
                                        'supportingDocument': {'sdId': previousCertSupJson["sdId"],
                                        'accessToken' : previousCertSupJson["accessToken"]}}]
                                       
    response = requests.request("POST", server_url + "/certify/updatePUD", cert = client_cert, headers=auth_header, json = payload)
    check_status(response)
    response_1 = response.json()[1]
    status = response_1['status']
    # Note that this endpoint uses "recieved", not "success" as positive result
    if(status != "received"):
        print ("Status: " + status)
    else:
        print("Updated Public Use Document successfully recieved by server")  
    return cert_supp, response



