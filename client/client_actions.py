import json
import globalenv
from models.certify_payload import Certify_Payload
from models.entropy_assessment import Entropy_Assessment
from models.supporting_document import Supporting_Document
from request_types.certify_requests import send_post_certify
from request_types.data_files import send_post_data_file
from request_types.entropy_assessments import send_post_entropy_registration
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

    # Parse EntropyAssessment
    entropy_assessment = globalenv.run_data["entropyAssessment"]
    data_files = globalenv.run_data["dataFiles"]
    numberOfOes = len(data_files)

    # Send Entropy registration(s) to server
    processed_eas = []
    for i in range(numberOfOes):
        processed_eas.append(send_post_entropy_registration(entropy_assessment))

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
        for cc in data_files[i]["conditioned"]:
            for ea in processed_eas[i].conditioned:

                if cc["sequencePosition"] == ea.sequence_position:
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

    # Parse and send Certify, body from run_file, ids from history
    certify_body = globalenv.run_data["certify"]

    entropy_assessments = []
    for ea in globalenv.run_data["history"]["entropyAssessments"]:
        entropy_assessments.append(Entropy_Assessment(ea["entropyAssessment"], oe_id=ea["oeId"], access_token=ea["accessToken"]))

    supporting_documentation = []
    for sd in globalenv.run_data["history"]["supportingDocumentation"]:
        supporting_documentation.append(Supporting_Document(sd["sdId"], access_token=sd["accessToken"]))

    certify_response = send_post_certify(Certify_Payload(certify_body["entropyId"], certify_body["moduleId"], certify_body["vendorId"], entropy_assessments, supporting_documentation))
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
