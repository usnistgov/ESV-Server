# Entropy Source Validation Client

The Entropy Source Validation Client is a means of automating the process in which third-party companies, vendors, and labs can communicate with the ESV server and receive an entropy source validation certificate. 

The client runs on the command line and requires Python 3.8+ 

#### Contents: 

1. **How to use** 
2. **Workflow** 
3. **Run-types** 
4. **Pre-requisites: Configuration and Run Files** 
5. **Alternative usages**

## 0. Some needed libraries 

```
pip3 install requests cryptography
```

The `requests` library is used to call the Web API. Version 2.27.1+

The `cryptography` library is used for Base64 and other methods related to TOTP. Version 36.0.1+

(Older versions of these libraries may work, but if you encounter problems, please upgrade to at least the version number listed above.)

## 1. How to use

The client takes in 3 arguments: The *run type*, the configuration file path (`--config_path`), and the run file path(`--run_path`).

There is a 4th optional argument for verbose mode: --verbose

The configuration and run file paths are optional and are only required if the user is not doing run types (status) or (certify). However, the files must still be in the same location as in the previous run.

An example command with the arguments is:

```
python3 client.py full --config_path config.json --run_path run.json --verbose
```

## 2. Workflow

Below is the general workflow for a full run with the client

1. Login / Authentication
2. Send Entropy Assessment Registration
3. Upload Data Files (Raw, Restart Test, Conditioning)
4. Check Data File Status
5. Upload Supporting Documentation
6. Certify (Optional)

## 3. Run-types

The client accepts different run-types, corresponding to a command, which are combinations of the above workflow. If certify is set to false in the configuration file, the full run will stop before the certify step. 

IDs such as Entropy Assessment and Data File IDs are printed as the client runs. They can also be found in the log file (located in the jsons folder), which stores values from the most recent run. 

The full run performs the full workflow and the other run types correspond to different sections of the workflow in the case that the user wants to perform another job at a different time (ex. submitting data files but not yet uploading supporting documentation).

- (`full`) Full Run
- (`status`) Check Data File Progress (of last run)
- (`submit`) Submit Entropy Assessment and Data Files
- (`support`) Upload Supporting Documentation
- (`certify`) Certify (Uses IDs from the last run)

## 4. Pre-requisites: Configuration and Run Files

The configuration and run files are JSONs that contain fields that the user must fill out before starting a run. Empty samples are available in the github folder 'jsons'. An example of each are shown below.

Note that only config.json and run.json are the only JSONs that should be filled out. The logs.json file should not be modified by hand.

## config file example

```
[
    {
        "TOTPPath": "<absolute path to totp seed>",
        "CertPath": "<absolute path to cert",
        "KeyPath": "<absolute path to key",
        "ServerURL": "https://demo.esvts.nist.gov:7443/esv/v1",
	    "EsvVersion": "1.0"
    }
]
```

## run file example

```
{
    "AssessmentRegistrationPath": "entropy-source-metadata.json",
    "DataFiles": [
        {
            "oeID":  <INT referring to the ID of the Operating Environment>,
            "rawNoisePath": "<absolute path to raw noise data file>",
            "restartTestPath": "<absolute path to restart data file>",
            "unvettedConditionedPaths": ["<absolute path to first unvetted data file>", "<absolute path to second unvetted data file>"]
        }
    ],
    "SupportingDocuments": [
        {
        "filePath": ["<absolute path to supporting documentation file"],
        "comment": ["..."],
        "sdType": ["EntropyAssessmentReport" or "PublicUseDocument" or "Other"]
        }
    ],
    "Certify": {
        "Certify": <BOOLEAN>,
        "moduleID": <INT referring to ID of module>,
        "vendorID": <INT referring to ID of vendor>,
        "entropyID": <STRING referring to ID of submitted Entropy ID>
    },
    "Assessment": {
        "numberOfAssessments": 1,
        "limitEntropyAssessmentToSingleModule": false
    },
    "PreviousRun": {
        "entr_jwt": "example",
        "df_ids": [
            "1"                
        ],
        "ea_id": "1",
        "cert_supp": [
            [
                {
                    "sdId": 1,
                    "accessToken": "example"
                }
            ]
        ]
	}
}
```

Note that DataFiles is an array. For submitting for multiple Operating Environments, create addition sets of oeID/rawNoisePath/restartTestPath/unvettedConditionedPaths.

## 5. Alternative usages

This client was designed to be all-inclusive, running the complete life cycle within itself from the initial submission through the certify request.  At each step, it saves information from the current stage in order to run future steps.

It is possible to use the web client to submit and the Python client although manually editting of the configuration file will be required.  If you have submitted an entropy asssessment and data file(s) through the web client and wish to check on the status, you will need to edit the run.json file manually.

In run.json, the "PreviousRun" property will need to be updated with information from the web client.  The ID of the Entropy Assessment will need to be added/modified at "ea_id". Any applicable data files will need to be placed at "df_ids" (as an array).

# License

NIST-developed software is provided by NIST as a public service. You may use, copy, and distribute copies of the software in any medium, provided that you keep intact this entire notice. You may improve, modify, and create derivative works of the software or any portion of the software, and you may copy and distribute such modifications or works. Modified works should carry a notice stating that you changed the software and should note the date and nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the source of the software.

NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED, IN FACT, OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT, AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE.

You are solely responsible for determining the appropriateness of using and distributing the software and you assume all risks associated with its use, including but not limited to the risks and costs of program errors, compliance with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of operation. This software is not intended to be used in any situation where a failure could cause risk of injury or damage to property. The software developed by NIST employees is not subject to copyright protection within the United States.
