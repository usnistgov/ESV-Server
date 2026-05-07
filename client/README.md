# Entropy Source Validation Client

The Entropy Source Validation Client is a means of automating the process in which third-party companies, vendors, and labs can communicate with the ESV Server and receive an entropy source validation certificate. The client runs on the command line and requires Python 3.8+.

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

The `requests` library is used to call the Web API. Version 2.27.1+ required. The `cryptography` library is used for Base64 and other methods related to TOTP. Version 36.0.1+ required. Older versions of these libraries may work, but if you encounter problems, please upgrade to at least the version number listed above.

## 1. How to use

During normal running, the client takes in 1 required argument (the run type) and several sometimes optional arguments:

- `run`: The type of operation to perform (e.g., `full`, `submit`, `status`).
- `--config_path`: Path to your configuration JSON file. This is required.
- `--run_path`: Path to your run JSON file. This is required.
- `--certificateId`: The number of the certificate requested (required for `getcertificate`).
- `--stats_90B_path`: Output file path for 90B statistical results JSON.
- `-v` or `--verbose`: Enable verbose mode for detailed logging.

An example command:

```
python3 client.py full --config_path config.json --run_path run.json --verbose
```

## 2. Workflow

### Entropy Assessment Workflow
1. Login / Authentication
2. Send Entropy Assessment Registration
3. Upload Data Files (Raw, Restart Test, Conditioning)
4. Check Data File Status
5. Upload Supporting Documentation
6. Certify

### Random Bit Generator (RBG) Workflow
1. Login / Authentication
2. Register Random Bit Generator
3. Upload Supporting Documentation
4. Check RBG Status
5. Certify RBG

### Post-certification Workflows
- Upload updated Public Use Document
- Add new Operating Environment (OE) to existing certificate
- View certificate

## 3. Run-types

The client accepts different run-types, which are combinations of the workflow steps.

### Entropy Assessment
- `full`: Full Run (Initial submission through certification).
- `submit`: Submit Entropy Assessment and Data Files (does not certify).
- `certify`: Certify a previously registered entropy source (Uses IDs from history).
- `fullAddOE`: Full run to add an OE to an existing entropy source certificate, and certify.
- `certifyAddOE`: Certify an added OE to an existing entropy source certificate (Uses IDs from history).
- `updatePUD`: Update the Public Use Document on an existing entropy source certificate.
- `status`: Check the status of previously submitted data files.

### Random Bit Generator (RBG)
- `submitRBG`: Register a random bit generator.
- `fullRBG`: Register and certify a random bit generator.
- `certifyRBG`: Certify a previously registered random bit generator.

### Combined
- `fullRBG_EA`: Register and certify both a random bit generator and an entropy source with data files.

### Utilities
- `support`: Upload Supporting Documentation.
- `getCertificate`: View an existing certificate. Requires `--certificateId`.
- `refresh`: Refreshes all tokens in the run file.

## 4. Pre-requisites: Configuration and Run Files

The configuration and run files are JSONs that contain fields the user must fill out. Empty samples are available in the `jsons` folder.

## config file example

```json
[
    {
        "TOTPPath": "/path/to/totp.seed",
        "CertPath": "/path/to/certificate.pem",
        "KeyPath": "/path/to/private.key",
        "ServerURL": "https://demo.esvts.nist.gov:7443/esv/v1",
        "EsvVersion": "1.0"
    }
]
```

## run file example

```json
{
    "entropyAssessment": {
        "primaryNoiseSource": "Example Source",
        "iidClaim": false,
        "bitsPerSample": 8,
        "hminEstimate": 1.0,
        "physical": true,
        "numberOfRestarts": 1000,
        "samplesPerRestart": 1000,
        "additionalNoiseSources": false,
        "conditioningComponent": [
            {
                "sequencePosition": 1,
                "vetted": false,
                "description": "Example CC",
                "bijectiveClaim": false,
                "minNin": 256,
                "minHin": 32.0,
                "nw": 128,
                "nOut": 128,
                "hOut": 31.997
            }
        ]
    },
    "dataFiles": [
        {
            "oeId": 1,
            "rawNoise": {
                "filePath": "/path/to/raw.bin",
                "bitsPerSample": 8
            },
            "restart": {
                "filePath": "/path/to/restart.bin",
                "bitsPerSample": 8
            },
            "conditioned": [
                {
                    "sequencePosition": 1,
                    "filePath": "/path/to/conditioned.bin",
                    "bitsPerSample": 8
                }
            ]
        }
    ],
    "randomBitGenerators": [
        {
            "construction": "RBG1",
            "allowsReseedRequests": true,
            "entropySources": {
                "combinationMethod": "Method1",
                "sources": [
                    {
                        "entropyValidations": "E1",
                        "entropyOperatingEnvironments": [1],
                        "rbgOperatingEnvironments": [1]
                    }
                ]
            },
            "drbg": {
                "validations": [
                    {
                        "validationNumber": "A1",
                        "algorithmOperatingEnvironments": [1]
                    }
                ],
                "algorithm": "HMAC_DRBG SHA2-256",
                "derivationFunction": true,
                "seed": [
                    {
                        "securityStrength": 128,
                        "minHin": 256,
                        "minNin": 256
                    }
                ],
                "reseed": true,
                "reseedFrequency": "hourly"
            },
            "operatingEnvironments": [1]
        }
    ],
    "supportingDocumentation": [
        {
            "filePath": "/path/to/doc.pdf",
            "comment": "Public Use Document",
            "sdType": "PublicUseDocument"
        }
    ],
    "certify": {
        "moduleId": 1,
        "vendorId": 1,
        "entropyId": "1234",
        "entropyCertificate": "E1"
    },
    "updatePublicUseDocument": {
        "entropyCertificate": "E1",
        "entropyId": "5678"
    }
}
```

* Note that `dataFiles` and `randomBitGenerators` are arrays.
* For multiple Operating Environments, create additional entries in the `dataFiles` array.
* The `updatePublicUseDocument` section is optional and used for the `updatePUD` run type.
* The `entropyCertificate` in the `certify` block is only expected for AddOE submissions. Its value is a string starting with 'E' followed by the certificate number (e.g., "E1").

## 5. Alternative usages

This client is designed to be all-inclusive. However, it is possible to use the web client for submission and the Python client for status checks or certification.

To do this, the `run.json` file must be manually updated. The `PreviousRun` (or equivalent historical tracking) property will need the correct `ea_id` (Entropy Assessment ID) and `df_ids` (Data File IDs) as an array, as obtained from the web client.

# License

NIST-developed software is provided by NIST as a public service. You may use, copy, and distribute copies of the software in any medium, provided that you keep intact this entire notice. You may improve, modify, and create derivative works of the software or any portion of the software, and you may copy and distribute such modifications or works. Modified works should carry a notice stating that you changed the software and should note the date and nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the source of the software.

NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED, IN FACT, OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT, AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE.

You are solely responsible for determining the appropriateness of using and distributing the software and you assume all risks associated with its use, including but not limited to the risks and costs of program errors, compliance with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of operation. This software is not intended to be used in any situation where a failure could cause risk of injury or damage to property. The software developed by NIST employees is not subject to copyright protection within the United States.
