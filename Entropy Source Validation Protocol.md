# Entropy Source Validation Protocol

The Entropy Source Validation Protocol is a means of communicating information about an entropy source to a validation server. The main use-case is to obtain an entropy source validation certificate to be publicly displayed as proof of conformance to the National Institute of Standards and Technology (NIST) [SP800-90B](). While the protocol is meant as an open standard for any number of servers, some configurable values are provided for a specific set of NIST run instances. The only `esvVersion` NIST servers support is `"1.0"`. 

## Table of Contents

1. Workflow
2. Authentication
3. Registering an Entropy Source
4. Submitting Files
5. Accessing the Demo Environment
6. Issues
7. Contributions
8. Disclaimer

## 1. Workflow

The first step for interacting with an ESV server is to login. Upon a completed login, a Java Web Token (JWT) is sent to the client and shall be used to authenticate the client for the remainder of the session. The next step is to register the entropy source with the server. The request shall contain general information about the noise source, and conditioning components used within the entropy source. The server will respond with a JWT for the specific entropy assessment, and at least two URLs to upload samples from various parts of the entropy source. The files may be uploaded in any order. Separately from the registration, other components are needed to obtain a validation certificate. Supporting documentation (Word or PDF) is also required to provide justification the entropy source meets the other requirements in SP800-90B. Information on the OE, Vendor, Module for the entropy source shall be provided to ACVTS and referenced via the ACVTS IDs when seeking a validation certificate. When the three elements are completed, the entropy assessment, the supporting documentation, and the entropy source metadata, the entropy source may be certified. 

## 2. Authentication

Authentication is handled with a two-factor system. The first is a certificate signed by a selected certificate authority for mutual TLS (mTLS). The certificates shall be present from both parties for all communications between the server and client. The second factor is a Time-based One Time Password (TOTP) according to [RFCX](). The chosen step is 30 seconds, and the 8 digits shall be in the generated password. The TOTP is only used for the initial login of the session, and to refresh and JWTs that may have expired. A JWT provides authentication for the current session and any objects created by the user. The server may provide claims embedded in the JWT which provide authorization for the specific user to access those objects. JWTs are set to expire 30 minutes after they are issued.

A user can login with the following request

``` POST /esv/v1/login```

with the following body:

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

to which the server shall respond with:

```
[
    {
        "esvVersion": "1.0"
    },
    {
        "accessToken": <jwt>
    }
]
```

To refresh an existing token send a request to

``` POST /esv/v1/login```

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

to which the server shall respond with:

```
[
    {
        "esvVersion": "1.0"
    },
    {
        "accessToken": <jwt>
    }
]
```

To all endpoints except for the `/login` endpoint, the JWT is expected to be within the header `Authorization` field as a bearer token. 

## 3. Registering an Entropy Source

Registering an entropy source creates an entropy assessment object that describes the entropy noise source and other components. It is recommended to have all data files ready for upload before sending the registration request.

To register a new entropy assessment send a request to

``` POST /esv/v1/entropyAssessments```

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
        "alphabetSize": 16,
        "hminEstimate": 3.1,
        "physical": true,
        "itar": false,
        "rawNoiseSHA256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "numberOfRestarts": 1000,
        "samplesPerRestart": 1000,
        "restartBitsSHA256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "additionalNoiseSources": false,
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
                "conditionedBitsSHA256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            },
            {
                "sequencePosition": 2,
                "vetted": true,
                "description": "AES-CBC-MAC",
                "validationNumber": "A0000",
                "minNin": 128,
                "minHin": 4,
                "nw": 128,
                "nOut": 128
            }
        ]
    }
]
```

to which the server shall respond with

```
[
    {
        "esvVersion": "1.0"
    },
    {
        "url": "/esvp/v1/entropyAssessments/<eaId>",
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
        "passed": false,
        "isSample": false,
        "accessToken": <jwt-with-claims>
    }
]
```

The valid properties within the top level of the registration are as follows

| JSON Property          | Description                                                                                | JSON Type  |
|------------------------|--------------------------------------------------------------------------------------------|------------|
| primaryNoiseSource     | 64 character description                                                                   | string     |
| iidClaim               | if the IUT claims the entropy source is [independent and identically distributed]()        | boolean    |
| bitsPerSample          | the number of bits per sample outputted by the noise source                                | integer    |
| alphabetSize           | the total number of distinct samples possibly outputted by the noise source                | integer    |
| hminEstimate           | an estimate of the number of bits of entropy outputted by the noise source over one sample | float      |
| physical               | if the noise source is physical or non-physical                                            | boolean    |
| itar                   | if the entropy source claims heightened security for an ITAR validation                    | boolean    |
| rawNoiseSHA256         | the SHA256 of the raw noise bits data file to be uploaded later                            | hex string |
| restartBitsSHA256      | the SHA256 of the restart bits data file to be uploaded later                              | hex string |
| numberOfRestarts       | the number of restarts used to generate the restart bits data file                         | integer    |
| samplesPerRestart      | the number of samples per restart used to generate the restart bits data file              | integer    |
| additionalNoiseSources | if additional noise sources are incorporated in the entropy source                         | boolean    |
| conditioningComponent  | an array of conditioning component objects described below                                 | object     |

The valid properties for the conditioning components are as follows

| JSON Property         | Description                                                                                                                                                  | JSON Type  |
|-----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|
| sequencePosition      | where in the potential chain of conditioning components it occurs, sequential starting at 1                                                                  | integer    |
| vetted                | whether the conditioning component is classified as a vetted conditioning component                                                                          | boolean    |
| bijectiveClaim        | this non-vetted conditioning component is a bijective function                                                                                               | boolean    |
| description           | brief description of the conditioning component, for a vetted conditioning component this shall be exactly the ACVTS name of the conditioning component mode | string     |
| validationNumber      | the ACVTS validation certificate number of the vetted conditioning component                                                                                 | string     |
| minNIn                | minimum bits inputted to the conditioning function                                                                                                           | integer    |
| minHIn                | minimum amount of entropy inputted to the conditioning function per the number of bits inputted                                                              | float      |
| nW                    | narrowest width of the conditioning function                                                                                                                 | integer    |
| nOut                  | number of bits outputted by the conditioning function                                                                                                        | integer    |
| conditionedBitsSHA256 | the SHA256 of the conditioning component bits data file to be uploaded later                                                                                 | hex string |

When a conditioning component is vetted, many of the options are restricted to singular values in accordance to [SP800-90B Section X]().

The `validationNumber` field is only applicable when `"vetted": true` is present. In this case, the `description` field must exactly match the ACVTS mode of the ConditioningComponent algorithm. The potential vetted functions can be found in [SP800-90B Section X]().

The `bijectiveClaim` field is only applicable when `"vetted": false` is present. A bijective conditioning component is one that neither adds nor removes entropy from the inputs passed in, as every input to the bijective function maps to exactly one output.

The `conditionedBitsSHA256` field is only applicable when `"vetted": false` is present. File upload is only required on non-vetted conditioning components, so a hash of the uploaded file is only expected at that time.

## 4. Submitting Files 

There are two types of files to be submitted to the server. Data files (files that contain random bits from the raw noise source, restart tests or conditioning components), or supporting documentation (that helps justify the claimed conformance to SP800-90B). File submissions are not via JSON like other ESV messages. Files are submitted via a `multipart/form-data` request. 

### Data Files

Data files are submitted after the entropy assessment has been registered.

These are done with a `POST /esv/v1/entropyAssessments/<eaId>/dataFiles/<dfId>` with the following body

```
Content-Type: multipart/form-data;
Key: dataFile, Value: <binary data file upload>
```

In the above case, the `<eaId>` and `<dfId>` are determined by the response from the server during the `POST /esv/v1/entropyAssessments` request. Multiple data file upload URLs will be provided by the server. The client is responsible for uploading the appropriate file to each URL. The files may be submitted in any order, but as the hashes are required in the previous `POST /esv/v1/entropyAssessments`, the files should be ready from the beginning.

### Supporting Documentation Files

Supporting documentation files are documents that explain the model behind the noise source in addition to other non-testable requirements of SP800-90B. The clients shall only upload Microsoft Word or PDF files: `.doc`, `.docx`, or `.pdf`. 

These are done with a `POST /esv/v1/supportingDocumentation` with the following body

```
Content-Type: multipart/form-data;
Key: itar, Value: <true/false>
Key: sdComments, Value: <string describing document, optional>
Key: sdFile, Value: <file upload, .doc, .docx, .pdf>
```

## 5. Accessing the Demo Environment

To access the demo server one needs an mTLS credential and a one-time password (OTP). 

To set expectations, since this is a demo system, it will be in a state of flux and any all data on the system is considered temporary and may be reset to accommodate development of the Entropy Source Validation Protocol (ESVP) service. We will try to keep the demo service relatively stable, but we plan to update it as we continue to add new features.

### Obtaining TLS credentials

To access the demo environment you will need to send a Certificate Signing Request (CSR) to us. Please use a 2048-bit RSA key pair and sign using at least a SHA-256 hash. Please send a request to esv-demo@nist.gov with 'ESV: DEMO CSR REQUEST' in the subject line. You will receive instructions for how to upload the CSR. You will receive a TOTP seed value along with the final certificate. 

You are expected to protect both the key pair and TOTP seed from unauthorized use and to notify NIST in the event that either becomes compromised. Also, since we do not have a formal login page the following notice applies when accessing the ESV system:

```
***WARNING***WARNING***WARNING

You are accessing a U.S. Government information system, which includes: 1) this computer, 2) this computer network,
3) all computers connected to this network, and 4) all devices and storage media attached to this network or to a
computer on this network. You understand and consent to the following: you may access this information system for
authorized use only; you have no reasonable expectation of privacy regarding any communication of data transiting 
or stored on this information system; at any time and for any lawful Government purpose, the Government may 
monitor, intercept, and search and seize any communication or data transiting or stored on this information system;
and any communications or data transiting or stored on this information system may be disclosed or used for any 
lawful Government purpose.

***WARNING***WARNING***WARNING”
```

## 6. Issues

Users are encouraged to submit issues to this repository. ESV developers will routinely check and communicate with users in the comment on those issues. If there is an issue you'd like to discuss privately, send an email to christopher.celi@nist.gov. 

## 7. Contributions

Change suggestions are welcome in Pull Requests.
