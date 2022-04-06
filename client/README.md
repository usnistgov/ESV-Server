# Entropy Source Validation Client

The Entropy Source Validation Client is a means of automating the process in which third-party companies, vendors, and labs can communicate with the ESV server and receive an entropy source validation certificate. 

The client runs on the command line and requires Python 3.8+ 

#### Contents: 

1. **How to use** 
2. **Workflow** 
3. **Run-types** 
4. **Pre-requisites: Configuration and Run Files** 

## 0. Some needed libraries 

```
pip3 install requests cryptography
```

The `requests` library is used to call the Web API.  

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
    "DataFiles": {
        "rawNoisePath": "<absolute path to raw noise data file>",
        "restartTestPath": "<absolute path to restart data file>",
        "unvettedConditionedPaths": ["<absolute path to first unvetted data file>", "<absolute path to second unvetted data file>"]
    },
    "SupportingDocuments": {
        "filePaths": ["<absolute path to supporting documentation file"],
        "comments": ["..."]
    },
    "Certify": {
        "Certify": true,
        "moduleID": 1,
        "vendorID": 1,
        "itar": false,
        "entropyID": "E123"
    },
    "Assessment": {
        "numberOfAssessments": 1,
        "oeID": 1,
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
