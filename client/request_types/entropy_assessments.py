import requests
from authentication.login import get_auth_header
from models.entropy_assessment import Conditioned_File, Entropy_Assessment
from utilities.utils import add_version_object, check_status, pretty_print
import globalenv

def send_post_entropy_registration(assessment_reg):

    print("\n***Sending Entropy Assessment Registration")

    if globalenv.verboseMode:
        print("Entropy Registration Outgoing:")
        pretty_print(assessment_reg)
    
    full_response = requests.post(globalenv.server_url + '/entropyAssessments', headers=get_auth_header(), cert=(globalenv.client_cert, globalenv.client_key), json=add_version_object(assessment_reg), verify=False)
    check_status(full_response)
    json_response = full_response.json()[1]     # Get rid of version object

    if globalenv.verboseMode:
        print("\n\nEntropy Registration Response:")
        pretty_print(json_response)

    # Reponse will be an array of entropy assessments based on the numberOfOEs, even if only one is present
    entropy_assessments = []
    for ea in json_response:
        ea_id, raw_noise_id, restart_id, conditioned = get_ids(ea)
        access_token = ea["accessToken"]
        entropy_assessments.append(Entropy_Assessment(ea_id, raw_noise_id=raw_noise_id, restart_id=restart_id, conditioned=conditioned, access_token=access_token))

    return entropy_assessments

# Gets and prints eaIDs and dfIDs after sending registration
def get_ids(response):
    
    # Get the end of the URL as the entropy assessment ID
    ea_id = response["url"].split("/")[-1]
    
    raw_noise_id = 0
    restart_id = 0
    conditioned = []

    for obj in response["dataFileUrls"]:

        # IDs are the end of the URLs
        if "rawNoiseBits" in obj:
            raw_noise_id = obj["rawNoiseBits"].split("/")[-1]

        if "restartTestBits" in obj:
            restart_id = obj["restartTestBits"].split("/")[-1]

        if "conditionedBits" in obj:
            conditioned.append(Conditioned_File(obj["conditionedBits"].split("/")[-1], int(obj["sequencePosition"])))

    print(f"Entropy Assessment ID: {ea_id}")
    print(f"Raw Noise Data File ID: {raw_noise_id}")
    print(f"Restart Data File ID: {restart_id}")
    for cc in conditioned:
        print(f"Conditioned Data File ID for sequence position {cc.sequence_position}: {cc.id}") 

    return ea_id, raw_noise_id, restart_id, conditioned