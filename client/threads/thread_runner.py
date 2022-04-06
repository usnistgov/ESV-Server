from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from threads.thread_functions import get_status, df_upload_cond, df_upload_raw, df_upload_restart, send_supp
from utilities.utils import log, check_status
import globalenv

class ThreadWrapper:

    #Step 4: Runner for threading stats
    def runner_stats(server_url, ea_id, df_ids, entr_jwt, client_cert):
        threads= []
        print("Getting Status...")
        print("Waiting for data file tests to complete...")
        with ThreadPoolExecutor(max_workers=20) as executor:
            for id in df_ids:
                threads.append(executor.submit(get_status, server_url, ea_id, id, entr_jwt, client_cert))
        
            #Check status codes of responses
            for task in as_completed(threads):
                check_status(task.result()) 
                
    #Step 3: Runner for threading data uploads       
    def runner_data(server_url, ea_id, df_ids, entr_jwt, conditioned, rawNoise, restartTest, client_cert):
        threads= []
        with ThreadPoolExecutor(max_workers=20) as executor:
            #Send raw and restart
            threads.append(executor.submit(df_upload_raw, server_url, ea_id, df_ids, entr_jwt, rawNoise, client_cert))
            threads.append(executor.submit(df_upload_restart, server_url, ea_id, df_ids, entr_jwt, restartTest, client_cert))
            #Send Conditioning
            for i in range(len(conditioned)):
                threads.append(executor.submit(df_upload_cond, server_url, ea_id, df_ids, entr_jwt, i, conditioned, client_cert))
            
            #Check status codes of responses
            for task in as_completed(threads):
                check_status(task.result()) 
            
            print("Data files submitted!\n")

    #Step 5: Runner for threading supporting docs uploads
    def runner_supp(comments, supporting_paths, itar, server_url, client_cert, auth_header):
        threads= []
        cert_supp = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            print('\nSending supporting documents')
            if len(comments) < len(supporting_paths): #Check formatting
                print("Error: Comments array must be the same length as that of the supporting file paths")
                exit()
            
            print("Your Supporting Documentation ID(s): ")
            #cert_supp = [] #Get and format IDs and JWTs for certify
            for i in range(len(supporting_paths)):
                threads.append(executor.submit(send_supp, comments[i], supporting_paths[i], itar, server_url, client_cert, auth_header))

            for task in as_completed(threads):
                #Check status code of responses and create cert_sup for certify
                supp_1, response = task.result()
                check_status(response)
                cert_supp.append(supp_1)

            log("cert_supp", cert_supp)
            return cert_supp
