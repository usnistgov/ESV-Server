# Entropy Source Validation (ESV)

This project is a hub for documentation, issues, and clients to interact with the NIST Entropy Source Validation Test System (ESVTS). An entropy source is a core component of a cryptographic module, providing the true randomness that is needed for crytographic algorithms to offer the security assurances for secure communication, data storage, etc. Evaluating the quality of an entropy source can be difficult. This project focuses on ensuring that entropy sources and random bit generators meet the requirements of [SP 800-90B](https://csrc.nist.gov/pubs/sp/800/90/b/final) and [SP 800-90C](https://csrc.nist.gov/pubs/sp/800/90/c/final) while [ACVTS](https://pages.nist.gov/ACVP) ensures that the Deterministic Random Bit Generators meet the requirements of [SP 800-90A](https://csrc.nist.gov/pubs/sp/800/90/a/r1/final). 

ESVTS is set up as a server with an API available to submit entropy sources and random bit generators for evaluation. This repository offers a Python client to access the API. A web-based client is also available at the API's URL. This repository is where issues should be reported on the ESVTS server even though the server code itself is not published here. Additionally ESVTS runs the [SP 800-90B Entropy Assessment Library](https://github.com/usnistgov/SP800-90B_EntropyAssessment) to analyze entropy sources. 

A Demo ESVTS is publicly available with credentials issued by request. Instructions to request credentials are under [Accessing the Demo Environment]. Prod ESVTS is available for [NVLAP-accredited Cryptography Security Testing Labs](https://csrc.nist.gov/Projects/testing-laboratories) featuring the 17ESV accreditation scope. The Prod ESVTS is how validation certificates are submitted that may eventually appear on [CSRC](https://csrc.nist.gov/Projects/cryptographic-module-validation-program/entropy-validations/search). 

## Protocol

The protocol for the ESVTS API is detailed in the [Entropy Source Validation Protocol](Entropy Source Validation Protocol.md). 

## Python Client

The Python client that can be used to access ESVTS is available in the [client](client/) directory. 

## Accessing the Demo Environment

To access the demo server one needs an mTLS credential and a one-time password (OTP). 

To set expectations, since this is a demo system, it will be in a state of flux and any all data on the system is considered temporary and may be reset to accommodate development of the Entropy Source Validation Protocol (ESVP) service. We will try to keep the demo service relatively stable, but we plan to update it as we continue to add new features.

The URL is https://demo.esvts.nist.gov:7443. 

### Obtaining TLS credentials

To access the demo environment you will need to send a Certificate Signing Request (CSR) to us. Please use a 2048-bit RSA key pair and sign using at least a SHA2-256 hash. Please send a request to esv-demo@nist.gov with 'ESV: DEMO CSR REQUEST' in the subject line. You will receive instructions for how to upload the CSR. You will receive a TOTP seed value along with the final certificate. Note, as of January 2025, credentials are shared with [ACVTS](https://pages.nist.gov/ACVP) but a request to expand the access permissions is still needed for esv-demo@nist.gov. 

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

## Issues

Users are encouraged to submit issues to this repository. ESV developers will routinely check and communicate with users in the comment on those issues. If there is an issue you'd like to discuss privately, send an email to christopher.celi@nist.gov. 

## Contributions

Change suggestions are welcome in Pull Requests.
