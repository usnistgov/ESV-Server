import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from threads.thread_functions import get_status, df_upload_cond, df_upload_raw, df_upload_restart, send_supp, send_updatedPud
from utilities.utils import log, check_status
import globalenv

class ThreadWrapper:

    #Step 4: Runner for threading stats
    def runner_stats(server_url, response, client_cert):
        ea_id = response.ea_id
        df_ids = response.df_ids
        entr_jwt = response.entr_jwt
        threads= []
        print("*** Getting Status")
        print("Waiting for data file tests to complete...")
        #Yvonne Cliff: Added file open to save SP 800-90B statistical test results to file
        with open(globalenv.stats_90B_path, 'a', encoding="utf-8") as stats_file:
            with ThreadPoolExecutor(max_workers=20) as executor:
                for id in df_ids:
                    threads.append(executor.submit(get_status, server_url, ea_id, id, entr_jwt, client_cert))

                #Check status codes of responses
                for task in as_completed(threads):
                    #Yvonne Cliff: Edited to save 90B statistical test results.
                    # Previously, code was:
                    #     check_status(task.result())
                    # Code was edited to save task.result() in myRes, then check status separately, 
                    # followed by printing the JSON code containing the 90B statistical test results.
                    myRes = task.result()
                    check_status(myRes)
                    if(globalenv.verboseMode):
                        print("[\'********** SP 800-90B Test Results **********\']")
                        print(myRes.json()) 
                        print("[\'********** END SP 800-90B Test Results **********\']")
                    stats_file.write(str(myRes.json()))
                    stats_file.write("\n\n")
    #Step 3: Runner for threading data uploads       
    def runner_data(server_url, responses, conditioned, rawNoise, restartTest, client_cert, rawNoiseSampleSize,restartSampleSize):
        ea_id = responses.ea_id
        df_ids = responses.df_ids
        entr_jwt = responses.entr_jwt
        threads= []
        with ThreadPoolExecutor(max_workers=20) as executor:
            #Send raw and restart
            threads.append(executor.submit(df_upload_raw, server_url, ea_id, df_ids, entr_jwt, rawNoise, client_cert, rawNoiseSampleSize))
            threads.append(executor.submit(df_upload_restart, server_url, ea_id, df_ids, entr_jwt, restartTest, client_cert,restartSampleSize))
            #Send Conditioning
            for i in range(len(conditioned)):
                conditionedSampleSize = -1
                threads.append(executor.submit(df_upload_cond, server_url, ea_id, df_ids, entr_jwt, i, conditioned, client_cert))
            
            #Check status codes of responses
            for task in as_completed(threads):
                check_status(task.result()) 
            
            print("Data files submitted!\n")

    #Step 5: Runner for threading supporting docs uploads
    def runner_supp(comments, sdType, supporting_paths, server_url, client_cert, auth_header):
        threads= []
        cert_supp = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            print('\n*** Sending supporting documents')
            if len(comments) < len(supporting_paths): #Check formatting
                print("Error: Comments array must be the same length as that of the supporting file paths")
                sys.exit(1)
            
            print("Supporting Documentation ID(s): ")
            #cert_supp = [] #Get and format IDs and JWTs for certify
            for i in range(len(supporting_paths)):
                threads.append(executor.submit(send_supp, comments[i], sdType[i], supporting_paths[i], server_url, client_cert, auth_header))

            for task in as_completed(threads):
                #Check status code of responses and create cert_sup for certify
                supp_1, response = task.result()
                check_status(response)
                cert_supp.append(supp_1)

            log("cert_supp", cert_supp)
            return cert_supp

#Step X: Runner for threading updated PUD uploads
    def runner_updatedPud(previousCertSup, entropyCertificate, entropyId, pud_path, server_url, client_cert, auth_header):
        threads= []
        cert_supp = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            print('\n*** Sending updated Public Use Document information')
            threads.append(executor.submit(send_updatedPud, previousCertSup, entropyCertificate, entropyId, pud_path, server_url, client_cert, auth_header))

            for task in as_completed(threads):
                #Check status code of responses and create cert_sup for certify
                supp_1, response = task.result()
                check_status(response)
                cert_supp.append(supp_1)

            log("cert_supp", cert_supp)
            return cert_supp
