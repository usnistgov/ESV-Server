# Entropy Source Validation Protocol

The Entropy Source Validation Protocol is a means of communicating information about an entropy source or random bit generator to a validation server. The first use case is to obtain an entropy source validation certificate to be publicly displayed as proof of conformance to the National Institute of Standards and Technology (NIST) [SP 800-90B](https://csrc.nist.gov/pubs/sp/800/90/b/final). The second is to obtain a Random Bit Generator certificate as proof of conformance to [SP 800-90C](https://csrc.nist.gov/pubs/sp/800/90/c/final). While the protocol is meant as an open standard for any number of servers, some configurable values are provided for a specific set of NIST run instances. The only protocol `esvVersion` NIST servers support is `"1.0"`. 

## Table of Contents

1. Workflow
2. Authentication
3. Registering an Entropy Source 
4. Registering a Random Bit Generator
5. Registering both an Entropy Source and Random Bit Generator
6. Submitting Files
7. Certify
8. Retrieving a Certificate

## 1. Workflow

The first step for interacting with an ESV server is to login. Upon a completed login, a JSON Web Token (JWT) is sent to the client and shall be used to authenticate the client for the remainder of the session. 

To submit only an entropy source to ESV, the next step is to register the entropy source with the server. The request shall contain general information about the noise source, and conditioning components used within the entropy source. The server will respond with a JWT for the specific entropy assessment, and at least two URLs to upload samples from various parts of the entropy source. The files may be uploaded in any order. Separately from the registration, other components are needed to obtain a validation certificate. Supporting documentation (Word or PDF) is also required to provide justification the entropy source meets the other requirements in SP 800-90B. Information on the OE, Vendor, Module for the entropy source shall be provided to ACVTS and referenced via the ACVTS IDs when seeking a validation certificate. When the three elements are completed, the entropy assessment, the supporting documentation, and the entropy source metadata, the entropy source may be certified. 

To submit only a random bit generator to ESV, after authentication the random bit generator must be registered with the server. The request shall contain information about the construction used, which entropy sources or randomness sources are used, and which deterministic random bit generators are available. This registration will depend on previously validated entropy sources or random bit generators, and deterministic random bit generators from ACVTS. Separately from the registration, supporting documentation is also required to provide justification the random bit generator meets the requirements of SP 800-90C. Along with some metadata such as the vendor and product name, these objects are packed together in a certify request to complete the process and begin the manual aspect of validation. 

It is also possible to submit both an entropy source and random bit generator simultaneously. The same requirements for each process apply however it is assumed that the random bit generator accepts only one entropy source, the one included in the same submission. 

## 2. Authentication

Authentication is handled with a two-factor system. The first is a certificate signed by a selected certificate authority for mutual TLS (mTLS). The certificates shall be present from both parties for all communications between the server and client. The second factor is a Time-based One Time Password (TOTP) according to [RFC-6238](https://datatracker.ietf.org/doc/html/rfc6238). The chosen step is 30 seconds, and the 8 digits shall be in the generated password. The TOTP is only used for the initial login of the session, and to refresh and JWTs that may have expired. A JWT provides authentication for the current session and any objects created by the user. The server may provide claims embedded in the JWT which provide authorization for the specific user to access those objects. JWTs are set to expire 30 minutes after they are issued.

A user can login with the following request

```POST /esv/v1/login```

with the following body

```
[
    {
        "esvVersion": <esv-version>
    },
    {
        "password": <totp>
    }
]
```

to which the server shall respond with

```
[
    {
        "esvVersion": <esv-version>
    },
    {
        "accessToken": <jwt>
    }
]
```

To refresh an existing token send a request to

```POST /esv/v1/login```

with the following body

```
[
    {
        "esvVersion": <esv-version>
    },
    {
        "password": <totp>,
        "accessToken": <jwt>
    }
]
```

to which the server shall respond with

```
[
    {
        "esvVersion": <esv-version>
    },
    {
        "accessToken": <new_jwt>
    }
]
```

A user may refresh multiple tokens at once with a request to 

```POST /esv/v1/login/refresh```

with the following body

```
[
    {
        "esvVersion": <esv-version>
    },
    {
        "password": <totp>,
        "accessToken": [<jwt1>, <jwt2>, ...]
    }
]
```

to which the server shall respond with 

```
[
    {
        "esvVersion": <esv-version>
    },
    {
        "accessToken": [<new_jwt1>, <new_jwt2>, ...]
    }
]
```

To all endpoints except for the `/login` endpoint, the JWT shall be within the header `Authorization` field as a bearer token. 

## 3. Registering an Entropy Source

Registering an entropy source creates an entropy assessment object that describes the entropy noise source and other components. It is recommended to have all data files ready for upload before sending the registration request.

To register a new entropy assessment send a request to

```POST /esv/v1/entropyAssessments```

with a body like the following

```
[
    {
        "esvVersion": <esv-version>
    },
    {
        "primaryNoiseSource": "ring oscillators",
        "iidClaim": false,
        "bitsPerSample": 4,
        "hminEstimate": 3.1,
        "physical": true,
        "numberOfRestarts": 1000,
        "samplesPerRestart": 1000,
        "additionalNoiseSources": false,
        "numberOfOEs": 1,
        "conditioningComponent": [
            {
                "sequencePosition": 1,
                "vetted": false,
                "bijectiveClaim": false,
                "description": "parallel XOR-ed LFSRs with output buffer",
                "minNin": 16,
                "minHin": 4,
                "nw": 16,
                "nOut": 8,
                "hOut": 7.5
            },
            {
                "sequencePosition": 2,
                "vetted": true,
                "description": "AES-CBC-MAC",
                "validationNumber": "A0000",
                "minNin": 128,
                "minHin": 4,
                "nw": 128,
                "nOut": 128,
                "hOut": 120
            }
        ]
    }
]
```

to which the server shall respond with

```
[
    {
        "esvVersion": <esv-version>
    },
    {
        "url": "/esv/v1/entropyAssessments/<eaId>",
        "createdOn": "2021-01-01T00:00:00.0000000-05:00",
        "expiresOn": "2021-01-31T00:00:00.0000000-05:00",
        "dataFileUrls": [
            {
                "rawNoiseBits": "/esv/v1/entropyAssessments/<eaId>/dataFiles/<dfId1>"
            },
            {
                "restartTestBits": "/esv/v1/entropyAssessments/<eaId>/dataFiles/<dfId2>"
            },
            {
                "conditionedBits": "/esv/v1/entropyAssessments/<eaId>/dataFiles/<dfId3>",
                "sequencePosition": 1
            }
        ],
        "publishable": false,
        "accessToken": <jwt-with-claims>
    }
]
```

The valid properties within the top level of the registration are as follows

| JSON Property          | Description                                                                                | JSON Type  |
|------------------------|--------------------------------------------------------------------------------------------|------------|
| primaryNoiseSource     | 64 character description of the primary noise source                                       | string     |
| iidClaim               | if the IUT claims the noise source produces [independent and identically distributed](https://en.wikipedia.org/wiki/Independent_and_identically_distributed_random_variables) samples       | boolean    |
| bitsPerSample          | the number of bits per sample output by the noise source                                   | integer    |
| hminEstimate           | an estimate of the number of bits of entropy output by the noise source over one sample    | float      |
| physical               | if the noise source is physical or non-physical                                            | boolean    |
| numberOfRestarts       | the number of restarts used to generate the restart bits data file                         | integer    |
| samplesPerRestart      | the number of samples per restart used to generate the restart bits data file              | integer    |
| additionalNoiseSources | if additional noise sources are incorporated in the entropy source                         | boolean    |
| numberOfOEs            | (OPTIONAL) number of Operating Environments for this metadata (defaults to 1)              | integer    | 
| conditioningComponent  | an array of conditioning component objects described below                                 | object     |

The valid properties for the conditioning components are as follows

| JSON Property         | Description                                                                                                                                                  | JSON Type  |
|-----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|
| sequencePosition      | where in the potential chain of conditioning components it occurs, sequential starting at 1                                                                  | integer    |
| vetted                | whether the conditioning component is classified as a vetted conditioning component                                                                          | boolean    |
| bijectiveClaim        | this non-vetted conditioning component is a bijective function                                                                                               | boolean    |
| description           | brief description of the conditioning component, for a vetted conditioning component this shall be exactly the ACVTS name of the conditioning component mode | string     |
| validationNumber      | the ACVTS validation certificate number of the vetted conditioning component                                                                                 | string     |
| minNIn                | minimum bits input to the conditioning function                                                                                                              | integer    |
| minHIn                | minimum amount of entropy input to the conditioning function per the number of bits input                                                                    | float      |
| nw                    | narrowest width of the conditioning function                                                                                                                 | integer    |
| nOut                  | number of bits output by the conditioning function                                                                                                           | integer    |
| hOut                  | number of bits of entropy output by the conditioning function                                                                                                | float      |

When a conditioning component is vetted, many of the options are restricted to singular values in accordance to [SP800-90B Section 3.1.5](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-90B.pdf).

The `validationNumber` field is only applicable when `"vetted": true` is present. In this case, the `description` field must exactly match the ACVTS mode of the ConditioningComponent algorithm. The potential vetted functions can be found in [SP800-90B Section 3.1.5.1.1](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-90B.pdf) or [SP 800-90 Updates](https://csrc.nist.gov/Projects/random-bit-generation/sp-800-90-updates).

Current supported vetted conditioning components (also reflected via [SP 800-90 Updates](https://csrc.nist.gov/Projects/random-bit-generation/sp-800-90-updates) for algorithms not directly cited in SP 800-90B):

| Conditioning Function | Vetted Conditioning Component(s) |
|-----------------------|----------------------------------|
| Hash	         | SHA1, SHA2-224, SHA2-256, SHA2-384, SHA2-512, SHA2-512t224, SHA2-512t256, SHA3-224, SHA3-256, SHA3-384, SHA3-512, Ascon-Hash256 |
| XOF            | SHAKE-128, SHAKE-256 |
| HMAC 	         | HMAC-SHA1, HMAC-SHA2-224, HMAC-SHA2-256, HMAC-SHA2-384, HMAC-SHA2-512, HMAC-SHA2-512t224, HMAC-SHA2-512t256, HMAC-SHA3-224, HMAC-SHA3-256, HMAC-SHA3-384, HMAC-SHA3-512 |
| Cipher	     | AES-CMAC, AES-CBC-MAC |
| CTR-DRBG	     | AES-128-CTR-DRBG, AES-192-CTR-DRBG, AES-256-CTR-DRBG |
| Hash-DRBG      | SHA2-224-Hash-DRBG, SHA2-256-Hash-DRBG, SHA2-384-Hash-DRBG, SHA2-512-Hash-DRBG, SHA2-512t224-Hash-DRBG, SHA2-512t256-Hash-DRBG, SHA3-224-Hash-DRBG, SHA3-256-Hash-DRBG, SHA3-384-Hash-DRBG, SHA3-512-Hash-DRBG |
| HMAC-DRBG      | SHA2-224-HMAC-DRBG, SHA2-256-HMAC-DRBG, SHA2-384-HMAC-DRBG, SHA2-512-HMAC-DRBG, SHA2-512t224-HMAC-DRBG, SHA2-512t256-HMAC-DRBG, SHA3-224-HMAC-DRBG, SHA3-256-HMAC-DRBG, SHA3-384-HMAC-DRBG, SHA3-512-HMAC-DRBG |
| Hash_df	     | Hash_DF |
| BlockCipher_df | BlockCipher_DF |

The `bijectiveClaim` field is only applicable when `"vetted": false` is present. A bijective conditioning component is one that neither adds nor removes entropy from the inputs passed in, as every input to the bijective function maps to exactly one output.

Data file upload is only allowed on non-vetted conditioning components.

## 4. Registering a Random Bit Generator

Registering a random bit generator creates an object on the server that can be submitted later for certification. 

To create the object referencing one or more existing entropy sources the following request is issued to `POST /esv/v1/rbg`

```
{
    "rbg": [
        {
            "construction": "RBG1, RBG2(P), RBG2(NP), RBG3(XOR), RBG3(RS), RBGC",
            "allowsReseedRequests": true,
            "entropySources": {
                "sources": ["E#"],
                "combinationMethod": "None or Method1 or Method2",
                "externalConditioningComponent": {
                    "procedure": "get_conditioned_input or get_conditioned_full_entropy_input",
                    "validationNumber": "A#",
                    "description": "",
                    "minNIn": 0,
                    "nOut": 0,
                    "minHIn": 0,
                    "hOut": 0,
                },
            },
            "drbg": {
                "validationNumber": ["A#"],
                "description": "",
                "derivationFunction": true,
                "seed": [
                    {
                        "securityStrength": 128,
                        "minHIn": 0,
                        "minNIn": 0
                    }
                ],
                "reseed": true,
                "reseedFrequency": "string",
            },
            "operatingEnvironments": []
        }
    ]
}
```

To create the object referencing an existing random bit generator the following payload is used instead

```
{
    "rbg": [
        {
            "construction": "RBG1, RBG2(P), RBG2(NP), RBG3(XOR), RBG3(RS), RBGC",
            "allowsReseedRequests": true,
            "randomnessSource": "G#",
            "drbg": {
                "validationNumber": ["A#"],
                "description": "",
                "derivationFunction": true,
                "seed": [
                    {
                        "securityStrength": 128,
                        "minHIn": 0,
                        "minNIn": 0
                    }
                ],
                "reseed": true,
                "reseedFrequency": "string",
            },
            "operatingEnvironments": []
        }
    ]
}
```

In both cases the response will be the resulting object and status

TBD Response

Here is a full list of the properties included in each `rbg` object:

| JSON Property                   | Description                                                                                                                     | JSON Type    |
|---------------------------------|---------------------------------------------------------------------------------------------------------------------------------|--------------|
| construction                    | The specific RBG Construction from SP 800-90C being validated                                                                   | string       |
| allowsReseedRequests            | Whether the RBG allows reseed requests from users                                                                               | boolean      |
| entropySources                  | An optional object outlining the entropy sources used. Only one of `entropySources` and `randomnessSource` shall be present.    | object       |
|   sources                       | An array of existing entropy validation certificates used by the RBG                                                            | string array |
|   combinationMethod             | The method by which the entropy sources are combined. Required only if multiple values are present in the `sources` list.       | string       |
|   externalConditioningComponent | An optional object outlining an external conditioning component                                                                 | object       |
|     procedure                   | The method from SP 800-90C stating how the conditioning component is run                                                        | string       |
|     validationNumber            | The algorithm validation number of the function used in the conditioning component                                              | string       |
|     description                 | The algorithm name used in the conditioning component                                                                           | string       |
|     minNin                      | The minimum number of bits used as input for each call of the conditioning component                                            | int          |
|     nOut                        | The number of bits provided as output from each call of the conditioning component                                              | int          |
|     minHin                      | The minimum number of entropy bits used as input for each call of the conditioning component                                    | float        |
|     hOut                        | The number of entropy bits provided as output from each call to the conditioning component                                      | float        |
| randomnessSource                | An existing random bit generator certificate that is used as input to the current random bit generator                          | string       |
| drbg                            | An object describing the deterministic random bit generator supported by the random bit generator                               | object       |
|   validationNumber              | An array of algorithm validation numbers of the deterministic random bit generator                                              | string array |
|   description                   | The algorithm name of the deterministic random bit generator                                                                    | string       |
|   derivationFunction            | Whether a derivation function is used by the deterministic random bit generator                                                 | boolean      |
|   seed                          | An array of objects describing how the deterministic random bit generator is seeded                                             | object array |
|     securityStrength            | Lists the security strength supported by the following properties while seeding                                                 | int          |
|     minNin                      | The minimum number of bits used as input to seed the deterministic random bit generator to the listed security strength         | int          |
|     minHin                      | The minimum number of entropy bits used as input to seed the deterministic random bit generator to the listed security strength | float        |
|   reseed                        | Whether the deterministic random bit generator can be reseeded during operation                                                 | boolean      |
|   reseedFrequency               | How frequently the deterministic random bit generator is reseeded                                                               | string       |
| operatingEnvironments           | An array of `operatingEnvironments` supported by the random bit generator                                                       | int array    |

Notes TBD on valid values.

## 6. Submitting Files 

There are two types of files to be submitted to the server. Data files (files that contain random bits from the raw noise source, restart tests or conditioning components), or supporting documentation (that helps justify the claimed conformance to SP 800-90B). File submissions are not via JSON like other ESV messages. Files are submitted via a `multipart/form-data` request. 

### 6.1 Data Files

Data files are submitted after the entropy assessment has been registered. Each file must contain exactly one million samples, padded to one byte per sample. In cases where the sample size of the data file does not match the overall entropy assessment bits per sample, the sample size of the data file can be specified via the key `dataFileSampleSize`. 

These are done with a `POST /esv/v1/entropyAssessments/<eaId>/dataFiles/<dfId>` with the following body

```
Content-Type: multipart/form-data;
Key: dataFileSampleSize, Value: <1-8>, Optional. If this value is not present, the value will be assumed as min(BitsPerSample, 8). This value must never be greater than BitsPerSample, or 8. 
Key: dataFile, Value: <binary data file upload>
```

In the above case, the `<eaId>` and `<dfId>` are determined by the response from the server during the `POST /esv/v1/entropyAssessments` request. Multiple data file upload URLs will be provided by the server. The client is responsible for uploading the appropriate file to each URL. The files may be submitted in any order, but as the hashes are required in the previous `POST /esv/v1/entropyAssessments`, the files should be ready from the beginning.

After a file has been submitted, a user may issue a `GET /esv/v1/entropyAssessments/<eaId>/dataFiles/<dfId>` to view the status of the submission through the testing process. Normally the file will complete entirely in about 5 minutes. There may be a handful of potential statuses displayed: 

* "Uploaded" - states that the file was received and no action has been taken yet. 
* "RunStarted" - indicates the testing has begun. 
* "Successful" - indicates the testing completed and will also display the results. 
* "Error" - will provide additional error information.

### 6.2 Supporting Documentation Files

Supporting documentation files are documents that explain the model behind the noise source in addition to other non-testable requirements of SP800-90B. The clients shall only upload Microsoft Word or PDF files: `.doc`, `.docx`, or `.pdf`. 

These are done with a `POST /esv/v1/supportingDocumentation` with the following body

```
Content-Type: multipart/form-data;
Key: sdFile, Value: <file upload, .doc, .docx, .pdf>
Key: sdType, Value: "EntropyAssessmentReport" or "PublicUseDocument" or "DataCollectionAttestation" or "RandomBitGeneratorReport" or "Other"
Key: sdComments, Value: <string describing document, optional but recommended when updating a Public Use Document>
```

TBD valid responses from server

## 7. Certify

### 7.1 Full Submission

Certify requests are done by `POST /esv/v1/certify`. The `moduleId` and `oeId` fields use ID numbers from the corresponding ACVTS environment. Thus, the "module" information and OE information must be previously registered to the ACVTS environment prior to this step. The EntropyID field is analagous to the Test Identifier (TID) in the module validation process. It helps the submitter track the entropy validation after it is submitted to the server. The `<eaId>` is determined by the response from the server during the `POST /esv/v1/entropyAssessments` request.

A certify request may have multiple supporting documents, or multiple entropy assessments. Each must include their accompanying JWT `accessToken`. The tokens may need to be refreshed before submitting. An example is the following...

```
[
    {
        "esvVersion": <esv-version>
    },
    {
        "limitEntropyAssessmentToSingleModule": false,
        "moduleId": 1,	
        "entropyId": "0000"
        "supportingDocumentation": [ 
            {"sdId": <sdId1>, "accessToken": "<jwt-with-claims-for-sdId1>"}
        ],
        "entropyAssessments": [			
            {
                "eaId": <eaId1>,
                "oeId": 1,
                "accessToken": "<jwt-with-claims-for-eaId1>"
            }
        ]          
    }
]
```

The response from the server will mirror the information sent, with the ACVTS IDs resolved to their values to allow quick confirmation of the data submitted.

The following properties are supported by the payload:

| JSON Property          | Description                                                                                | JSON Type  |
|------------------------|--------------------------------------------------------------------------------------------|------------|
| limitEntropyAssessmentToSingleModule | boolean stating whether the entropy assessment associated with this certification is applicable to a single module / vendor | boolean |
| moduleId               | refers to the module ID number of the corresponding ACVTS environment                      | integer    |
| entropyId              | analagous to the Test Identifier (TID) in the module validation process, used by submitter to track review progress | string |
| sdId (multiple)        | ID of the supporting document which was returned upon submission of supporting document(s) | integer    |
| accessToken (supportingDocumentation) | the jwt with claims for the corresponding sdId                              | string     | 
| eaId                   | corresponds to the response from the server during the POST /esv/v1/entropyAssessments request | integer |
| oeId					 | refers to the operating environment ID number from the corresponding ACVTS environment     | integer    |
| accessToken (entropyAssessments) | the jwt with claims for the corresponding eaId                                   | string |

### 7.2 AddOE

This certify request allows a user to add Operating Environments (OEs) to an existing certificate. The cost recovery associated with this request is the EntropyUpdate (EU). Note, the review will be performed to the current guidance, not necessarily the guidance available at the time of the original submission. The properties for the submission are the same as a Full Submission, except the `"moduleId"` is replaced with the existing `"entropyCertificate"`. 

The request is a `POST` on `/esv/v1/certify/addOE` or `/esv/v1/certify/addOperatingEnvironment`.

```
[
    {
        "esvVersion": <esv-version>
    },
    {
        "limitEntropyAssessmentToSingleModule": false,
        "entropyCertificate": "E999",	
        "entropyId": "0000"
        "supportingDocumentation": [ 
            {"sdId": <sdId1>, "accessToken": "<jwt-with-claims-for-sdId1>"}
        ],
        "entropyAssessments": [			
            {
                "eaId": <eaId1>,
                "oeId": 1,
                "accessToken": "<jwt-with-claims-for-eaId1>"
            }
        ]          
    }
]
```

The following additional properties are supported by the payload compared to the Full Submission above:

| JSON Property      | Description                                            | JSON Type |
|--------------------|--------------------------------------------------------|-----------|
| entropyCertificate | string representation of the certificate to be updated | string    |

### 7.3 UpdatePUD

This certify request allows a user to request that a new Public Use Document (PUD) is attached to an existing certificate. This can be helpful for corrections or rebranding. There is no cost recovery associated with this request. When the PUD is uploaded to the supportingDocumentation endpoint, the document must be uploaded with the PUD document type. Please include a comment on what changed in the document compared to the existing PUD. This will greatly expedite the review process. 

The request is a `POST` on `/esv/v1/certify/updatePUD` or `/esv/v1/certify/updatePublicUseDocument`.

```
[
    {
        "esvVersion": <esv-version>>
    },
    {
        "entropyCertificate": "E999",
        "entropyId": "0000",
        "supportingDocument":  
        {
            "sdId": <sdId1>,
            "accessToken": "<jwt-with-claims-for-sdId1>"
        }
    }
]
```

A positive response is the simple acknowledgement.

```
[
    {
        "esvVersion": "1.0"
    },
    {
        "status": "received"
    }
]
```

The following properties are supported by an UpdatePUD request. 

| JSON Property                   | Description                                                                                                  | JSON Type |
|---------------------------------|--------------------------------------------------------------------------------------------------------------|-----------|
| entropyCertificate              | string representation of the certificate to be updated                                                       | string    |
| entropyId                       | analagous to the Test Identifier (TID) in the module validation process, used by submitter to track progress | string    |
| supportingDocument              | an object for the supporting document information                                                            | object    |
| sdId (supportingDocument)       | ID of the supporting document which was returned upon submission of supporting document                      | integer   |
| accessToken (supportingDocument)| the jwt with claims for the corresponding sdId                                                               | string    |

## 8. Getting Entropy Certificate Information

To look up entropy certificate information through the API, a user may send the following request:

`GET` on `/esv/v1/entropyCertificate/E#` where `#` is the certificate number as shown on https://csrc.nist.gov. 

The response on a valid certificate is the following basic information about the certificate. 

```
[
    {
        "esvVersion": <esv-version>
    },
    {
        "certificateId": 1,
        "certificateNumber": 999,
        "isPhysical": false,
        "isReusable": true
    }
]
```
