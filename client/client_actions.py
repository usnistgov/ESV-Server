import json
from time import sleep
from authentication.login import refresh_jwt
import globalenv
from models.entropy_certify_payload import Entropy_Certify_Payload
from models.entropy_assessment import Entropy_Assessment
from models.random_bit_generator import Random_Bit_Generator
from models.rbg_certify_payload import Rbg_Certify_Payload
from models.supporting_document import Supporting_Document
from request_types.certificates import send_get_entropy_certificate
from request_types.certify_requests import send_post_certify, send_post_certify_add_oe, send_post_certify_rbg
from request_types.data_files import send_post_data_file
from request_types.entropy_assessments import send_post_entropy_registration
from request_types.random_bit_generators import send_get_random_bit_generator, send_post_random_bit_generator
from request_types.supporting_documentation import send_all_supp_doc, send_post_update_pud
from threads.thread_runner import runner_stats
from utilities.utils import pretty_print


def clear_history():
    if "history" in globalenv.run_data:
        print(f"history already present in {globalenv.run_path}, remove in order to re-run")
        exit(1)

    # Create record for IDs and access tokens
    globalenv.run_data["history"] = {}

def register_entropy_assessment():
    if "entropyAssessment" not in globalenv.run_data:
        print(f"entropyAssessment not found in {globalenv.run_path}")
        exit(1)

    if "dataFiles" not in globalenv.run_data:
        print(f"dataFiles not found in {globalenv.run_path}")
        exit(1)

    if "numberOfOEs" in globalenv.run_data["entropyAssessment"]:
        print("numberofOEs must be removed from the entropyAssessment, it will be computed automatically by the data files provided")
        exit(1)

    # Parse EntropyAssessment
    entropy_assessment = globalenv.run_data["entropyAssessment"]
    data_files = globalenv.run_data["dataFiles"]
    numberOfOes = len(data_files)

    if globalenv.verboseMode:
        print(f"Number of OEs detected: {numberOfOes}")

    # Send Entropy registration(s) to server
    # Client sends each OE individually, so there should only ever be one object in the returned array
    processed_eas = []
    for i in range(numberOfOes):
        processed_eas.append(send_post_entropy_registration(entropy_assessment)[0])

    # Send data files to server
    if len(data_files) != len(processed_eas):
        print("Error: mismatched data files and processed entropy assessments")
        exit(1)

    data_file_ids = []
    for i in range(len(data_files)):
        processed_eas[i].oe_id = data_files[i]["oeId"]

        #ea_id, df_id, file_path, bits_per_sample = 0
        raw_bits_per_sample = 0
        if "bitsPerSample" in data_files[i]["rawNoise"]:
            raw_bits_per_sample = data_files[i]["rawNoise"]["bitsPerSample"]

        send_post_data_file(processed_eas[i].ea_id, processed_eas[i].raw_noise_id, data_files[i]["rawNoise"]["filePath"], processed_eas[i].access_token, raw_bits_per_sample)
        data_file_ids.append((processed_eas[i].ea_id, processed_eas[i].raw_noise_id, processed_eas[i].access_token))

        restart_bits_per_sample = 0
        if "bitsPerSample" in data_files[i]["restart"]:
            restart_bits_per_sample = data_files[i]["restart"]["bitsPerSample"]

        send_post_data_file(processed_eas[i].ea_id, processed_eas[i].restart_id, data_files[i]["restart"]["filePath"], processed_eas[i].access_token, restart_bits_per_sample)
        data_file_ids.append((processed_eas[i].ea_id, processed_eas[i].restart_id, processed_eas[i].access_token))

        # Need to cycle through the pairing to find where the sequence positions match in the event that the order isn't consistent
        # Different get() because this property may or may not exist depending on the registration
        for cc in data_files[i].get("conditioned", []):
            for ea in processed_eas[i].conditioned:

                if int(cc["sequencePosition"]) == ea.sequence_position:
                    cc_bits_per_sample = 0
                    if "bitsPerSample" in cc:
                        cc_bits_per_sample = cc["bitsPerSample"]

                    send_post_data_file(processed_eas[i].ea_id, ea.id, cc["filePath"], processed_eas[i].access_token, cc_bits_per_sample)
                    data_file_ids.append((processed_eas[i].ea_id, ea.id, processed_eas[i].access_token))

    # Wait for all data files to finish...
    runner_stats(data_file_ids)

    # Store IDs and access tokens in history object
    globalenv.run_data["history"]["entropyAssessments"] = []
    for ea in processed_eas:
        ea_history = {}
        ea_history["entropyAssessment"] = ea.ea_id
        ea_history["oeId"] = ea.oe_id
        ea_history["accessToken"] = ea.access_token
        ea_history["rawNoiseId"] = ea.raw_noise_id
        ea_history["restartId"] = ea.restart_id
        ea_history["conditionedIds"] = []
        for cc in ea.conditioned:
            cc_obj = {}
            cc_obj["id"] = cc.id
            cc_obj["sequencePosition"] = cc.sequence_position
            ea_history["conditionedIds"].append(cc_obj)

        globalenv.run_data["history"]["entropyAssessments"].append(ea_history)

    with open(globalenv.run_path, 'w', encoding="utf-8") as run_file:
        run_file.write(json.dumps(globalenv.run_data, indent=4))

def display_data_file_status(retry=True):
    if "history" not in globalenv.run_data:
        print(f"history not present in {globalenv.run_path}, needs to be present to retrieve data file ids")
        exit(1)

    if "entropyAssessments" not in globalenv.run_data["history"]:
        print(f"entropyAssessments not present in {globalenv.run_path} history, needs to be present to retrieve data file ids")
        exit(1)

    # Get all the data file ids from history [(ea_id, df_id, jwt)]
    data_files = []
    for ea in globalenv.run_data["history"]["entropyAssessments"]:
        data_files.append((ea["entropyAssessment"], ea["rawNoiseId"], ea["accessToken"]))
        data_files.append((ea["entropyAssessment"], ea["restartId"], ea["accessToken"]))

        for cc in ea["conditionedIds"]:
            data_files.append((ea["entropyAssessment"], cc["id"], ea["accessToken"]))

    # Run the multi-threaded stat runner
    runner_stats(data_files, retry)

def submit_supporting_documentation():
    if "supportingDocumentation" not in globalenv.run_data:
        print(f"supportingDocumentation not found in {globalenv.run_path}")
        exit(1)

    # Parse and send SupportingDocumentation
    supporting_documents = globalenv.run_data["supportingDocumentation"]
    supp_responses = send_all_supp_doc(supporting_documents)

    # Store IDs and access tokens in run file
    globalenv.run_data["history"]["supportingDocumentation"] = [{"sdId": resp.sd_id, "sdType": resp.sd_type, "accessToken": resp.access_token} for resp in supp_responses]
    with open(globalenv.run_path, 'w', encoding="utf-8") as run_file:
        run_file.write(json.dumps(globalenv.run_data, indent=4))

def certify_entropy_assessment():
    if "certify" not in globalenv.run_data:
        print(f"certify not found in {globalenv.run_path}")
        exit(1)

    if "history" not in globalenv.run_data:
        print(f"history not found in {globalenv.run_path}")
        exit(1)

    # Parse and send Certify, body from run_file, ids from history
    certify_body = globalenv.run_data["certify"]

    entropy_assessments = []
    for ea in globalenv.run_data["history"]["entropyAssessments"]:
        entropy_assessments.append(Entropy_Assessment(ea["entropyAssessment"], oe_id=ea["oeId"], access_token=ea["accessToken"]))

    supporting_documentation = []
    for sd in globalenv.run_data["history"]["supportingDocumentation"]:
        supporting_documentation.append(Supporting_Document(sd["sdId"], access_token=sd["accessToken"]))

    certify_response = send_post_certify(Entropy_Certify_Payload(certify_body["entropyId"], entropy_assessments, supporting_documentation, module_id=certify_body["moduleId"], vendor_id=certify_body["vendorId"]))
    if globalenv.verboseMode:
        pretty_print(certify_response)

    print("Submission complete")

# TODO this could be de-duplicated with the above with some added logic to perform the branching as needed
def certify_entropy_assessment_add_oe():
    if "certify" not in globalenv.run_data:
        print(f"certify not found in {globalenv.run_path}")
        exit(1)

    if "history" not in globalenv.run_data:
        print(f"history not found in {globalenv.run_path}")
        exit(1)

    # Parse and send Certify, body from run_file, ids from history
    certify_body = globalenv.run_data["certify"]

    entropy_assessments = []
    for ea in globalenv.run_data["history"]["entropyAssessments"]:
        entropy_assessments.append(Entropy_Assessment(ea["entropyAssessment"], oe_id=ea["oeId"], access_token=ea["accessToken"]))

    supporting_documentation = []
    for sd in globalenv.run_data["history"]["supportingDocumentation"]:
        supporting_documentation.append(Supporting_Document(sd["sdId"], access_token=sd["accessToken"]))

    certify_response = send_post_certify_add_oe(Entropy_Certify_Payload(certify_body["entropyId"], entropy_assessments, supporting_documentation, entropy_certificate=certify_body["entropyCertificate"]))
    if globalenv.verboseMode:
        pretty_print(certify_response)

    print("Submission complete")    

def certify_update_public_use_document():
    if "updatePublicUseDocument" not in globalenv.run_data:
        print(f"updatePublicUseDocument not found in {globalenv.run_path}")
        exit(1)

    # Grab settings from run file
    update_pud = globalenv.run_data["updatePublicUseDocument"]

    # Grab PublicUseDocument info from history
    pud = None
    for sd in globalenv.run_data["history"]["supportingDocumentation"]:
        if sd["sdType"] == "PublicUseDocument":
            pud = Supporting_Document(sd["sdId"], access_token=sd["accessToken"])

    send_post_update_pud(update_pud["entropyCertificate"], update_pud["entropyId"], pud.sd_id, pud.access_token)

def display_entropy_certificate(certificateId):

    if certificateId == None:
        print("Error: CertificateId not provided. Use --certificateId [id] on commandline to set. For example --certificateId E0\n")
        exit(1)

    send_get_entropy_certificate(certificateId)
    
def refresh_tokens():
    if "history" not in globalenv.run_data:
        print(f"history not present in {globalenv.run_path}, needs to be present to retrieve access tokens")
        exit(1)

    # Get all JWTs from history
    history = globalenv.run_data["history"]
    jwts = []

    # TODO
    # Unfortunately there's no way to check if a JWT is valid without querying the server, so we will always refresh all tokens
    # The downside means that some requests will always take 30 seconds because the login uses the TOTP window immediately before
    # the token refresh. 
    # This could theoretically be fixed by adjusting the execution path for refresh_tokens to replace login when needed.
    # The only danger is cases where a globalenv JWT (without claims) may be needed because it will not be prepared as usual. 

    if "entropyAssessments" in history:
        for ea in history["entropyAssessments"]:
            jwts.append(ea["accessToken"])

    if "supportingDocumentation" in history:
        for sd in history["supportingDocumentation"]:
            jwts.append(sd["accessToken"])

    print(f"{len(jwts)} tokens found, refreshing now...")

    # Refresh JWTs, order of the input list is maintained
    new_jwts = refresh_jwt(jwts)
    index = 0

    # Write back to history
    if "entropyAssessments" in history:
        for ea in history["entropyAssessments"]:
            ea["accessToken"] = new_jwts[index]
            index += 1

    if "supportingDocumentation" in history:
        for sd in history["supportingDocumentation"]:
            sd["accessToken"] = new_jwts[index]
            index += 1

    print(f"{len(new_jwts)} tokens refreshed")

    globalenv.run_data["history"] = history
    with open(globalenv.run_path, 'w', encoding="utf-8") as run_file:
        run_file.write(json.dumps(globalenv.run_data, indent=4))

def register_random_bit_generator():
    if "randomBitGenerators" not in globalenv.run_data:
        print(f"randomBitGenerators not found in {globalenv.run_path}")
        exit(1)

    # Send payload to server
    rbg = globalenv.run_data["randomBitGenerators"]
    processed_rbg = send_post_random_bit_generator(rbg)

    # Store ID and access token in history object
    globalenv.run_data["history"]["randomBitGenerators"] = {}
    globalenv.run_data["history"]["randomBitGenerators"]["rbgId"] = processed_rbg.rbg_id
    globalenv.run_data["history"]["randomBitGenerators"]["accessToken"] = processed_rbg.access_token

    with open(globalenv.run_path, 'w', encoding="utf-8") as run_file:
        run_file.write(json.dumps(globalenv.run_data, indent=4))

def get_random_bit_generator(retry=True):
    if "history" not in globalenv.run_data:
        print(f"history not found in {globalenv.run_path}")
        exit(1)

    rbg = Random_Bit_Generator(globalenv.run_data["history"]["randomBitGenerators"]["rbgId"], globalenv.run_data["history"]["randomBitGenerators"]["accessToken"])
    
    first_request = True
    while retry or first_request:
        retrieved_rbg = send_get_random_bit_generator(rbg)
        first_request = False

        if ("retry" not in retrieved_rbg):
            # Retrieved RBG successfully, no more retrying
            retry = False

            if globalenv.verboseMode:
                print("\n\nRBG GET Response:")
                pretty_print(retrieved_rbg)

        else:
            print(f"RBG {retrieved_rbg['rbgId']} not yet available, retrying in 30 seconds...")
            sleep(30)

def certify_random_bit_generator():
    if "certify" not in globalenv.run_data:
        print(f"certify not found in {globalenv.run_path}")
        exit(1)

    if "history" not in globalenv.run_data:
        print(f"history not found in {globalenv.run_path}")
        exit(1)
        
    # Parse and send Certify, body from run_file, ids from history
    certify_body = globalenv.run_data["certify"]
    rbg_history = globalenv.run_data["history"]["randomBitGenerators"]
    rbg = Random_Bit_Generator(rbg_history["rbgId"], rbg_history["accessToken"])
    
    supporting_documentation = []
    for sd in globalenv.run_data["history"]["supportingDocumentation"]:
        supporting_documentation.append(Supporting_Document(sd["sdId"], access_token=sd["accessToken"]))

    certify_response = send_post_certify_rbg(Rbg_Certify_Payload(certify_body["entropyId"], rbg, supporting_documentation,  module_id=certify_body["moduleId"], vendor_id=certify_body["vendorId"]))
    if globalenv.verboseMode:
        pretty_print(certify_response)

    print("Submission complete")  

# TODO
def certify_combined_rbg_ea():
    x = 1
