from concurrent.futures import ThreadPoolExecutor, as_completed
from request_types.data_files import send_get_data_file_status
from utilities.utils import check_status, pretty_print
import globalenv

# File sets come in as [(ea_id, df_id, jwt)]
def runner_stats(file_sets):
    threads= []
    print("*** Getting Status")
    print("Waiting for data file tests to complete...")
    
    # Yvonne Cliff: Added file open to save SP 800-90B statistical test results to file
    with ThreadPoolExecutor(max_workers=20) as executor:
        for file_tuple in file_sets:
            threads.append(executor.submit(send_get_data_file_status, file_tuple[0], file_tuple[1], file_tuple[2]))

        #Check status codes of responses
        for task in as_completed(threads):

            myRes = task.result()
            check_status(myRes)
            if(globalenv.verboseMode):
                print("[\'********** SP 800-90B Test Results **********\']")
                pretty_print(myRes.json()[1]) 
                print("[\'********** END SP 800-90B Test Results **********\']")

            # Yvonne Cliff: Edited to save 90B statistical test results.
            if globalenv.record_90B_stats:
                with open(globalenv.stats_90B_path, 'a', encoding="utf-8") as stats_file:
                    stats_file.write(str(myRes.json()))
                    stats_file.write("\n\n")

    