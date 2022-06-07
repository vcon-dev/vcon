# vcon
The Home Repo for vCons

## Introduction
Its all about conversations and capturing them in a standardized container.

See the [white paper](https://docs.google.com/document/d/1TV8j29knVoOJcZvMHVFDaan0OVfraH_-nrS5gW4-DEA/edit?usp=sharing)

See the [key note proposal for vCons](https://blog.tadsummit.com/2021/12/08/strolid-keynote-vcons/).

## Table of Contents
* [Example Code](#example-code)
    * [Example Simple vCon Construction](#example-simple-vcon-construction)
    * [Example vCon signing](#example-vcon-signing)
    * [Example Verification of Signed vCon](#example-verification-of-signed-vcon)
* [Test Certficates](#test-certificates)

## Example Code

### Example Simple vCon Construction
```python:
import vcon

# Construct empty vCon
vCon = vcon.Vcon()

# Add some basic call META data
caller = "+18881234567"
called = "1234"
vCon.set_party_tel_url(caller)
vCon.set_party_tel_url(called)

# Add a recording of the call
recording_name = "call_recording.wav"
with open(file_name, 'r') as file_handle:
      recording_bytes = file_handle.read()
vCon.add_dialog_inline_recording(
  recording_bytes,
  "Mon, 23 May 2022 20:09:01 -0000",
  23.5, # sec. duration
  [0, 1], # parties recorded
  "audio/x-wav", # MIME type
  recording_name)

# Serialize the vCon to a JSON format string
json_string = vCon.dumps()
```

### Example vCon signing

```python:
# sign a vCon
cert_chain_file_names = ["signer.crt", "issuer.crt", "ca_root.crt"]
private_key_file_name = "signer.key"
vCon.sign(cert_chain_file_names, private_key_file_name)

# NOTE: vCon is now read only

# serialize the signed vCon
signed_vcon_json = vCon.dumps()
```

### Example Verification of Signed vCon

```python:
# Construct a vCon from a signed vCon JSON string
signed_vcon = vcon.Vcon()
signed_vcon.loads(signed_vcon_json)

# NOTE: cannot read signed vCon data until it is verified

# Verify the signed vCon 
ca_list = ["ca.crt"]
signed_vcon.verify(ca_list)
```

## Test Certifcates
A set of certifcates have been created for the purpose of testing the signing and verification of vCons using the vcon python package.  The certifcates and their private keys can be found [here](certs).  DO NOT USE THESE CERTIFICATES OR KEYS IN PRODUCTION.  They are for TESTING ONLY!!!!

You can substitue the following values in the variables in the above examples, if you would like to use the test certs and keys:
```python:
cert_chain_file_names = ["certs/fake_grp.crt", "certs/fake_div.crt", "ca_root.crt"]
private_key_file_name = "certs/fake_grp.key"
ca_list = ["certs/fake_ca_root.crt"]
```

