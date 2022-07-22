""" Unit tests for JWE encrypted vCon """

import pytest
import vcon
import json
import typing

DIVISION_CERT = "certs/fake_div.crt"
DIVISION_PRIVATE_KEY = "certs/fake_div.key"

call_data = {
      "epoch" : "1652552179",
      "destination" : "2117",
      "source" : "+19144345359",
      "rfc2822" : "Sat, 14 May 2022 18:16:19 -0000",
      "rfc3339" : "2022-05-14T18:16:19.000+00:00",
      "file_extension" : "WAV",
      "duration" : 94.84,
      "channels" : 1
}

@pytest.fixture(scope="function")
def empty_vcon() -> vcon.Vcon:
  """ construct vCon with no data """
  vCon = vcon.Vcon()
  return(vCon)

@pytest.fixture(scope="function")
def two_party_tel_vcon(empty_vcon : vcon.Vcon) -> vcon.Vcon:
  """ construct vCon with two tel URL """
  vCon = empty_vcon
  first_party = vCon.set_party_tel_url(call_data['source'])
  second_party = vCon.set_party_tel_url(call_data['destination'])
  return(vCon)

import jose.jwe
import secrets
import cryptography.x509

def build_encryption_jwk_from_pem_file(cert_pem_file_name : str) -> dict:

  pem_string = vcon.security.load_string_from_file(cert_pem_file_name)

  public_key_object = cryptography.x509.load_pem_x509_certificate(bytes(pem_string, "utf-8"))

  #algorithm = "RS256"
  #algorithm = "RSA1_5"
  algorithm = "RSA-OAEP"

  encryption_key = {}
  encryption_key["kty"] = "RSA"
  encryption_key["alg"] = algorithm
  encryption_key["n"] = jose.utils.base64url_encode(jose.utils.long_to_bytes(public_key_object.public_key().public_numbers().n)).decode('utf-8')
  encryption_key["e"] = jose.utils.base64url_encode(jose.utils.long_to_bytes(public_key_object.public_key().public_numbers().e)).decode('utf-8')
  encryption_key["kid"] = public_key_object.subject.get_attributes_for_oid(cryptography.x509.NameOID.COMMON_NAME)[0].value

  return(encryption_key)

def jwe_compact_token_to_complete_serialization(jwe_token : str, enc : str = "", x5c : typing.List[str] = []) -> dict:
  """
  Convert a JWE dot separated token to a JWE complete serialization

  Returns:
    dict containing Complete JWE JSON Serialization Representation
  """

  (protected, content_encrypted_key, iv, cyphertext, authentication_tag) = jwe_token.split('.')
  #(header, encrypted_key, recip_iv, recip_cyphertext, recip_authentication_tag) = jwe_token.split('.')

  jwe_complete_serialization = {}
  jwe_complete_serialization["protected"] = protected
  jwe_complete_serialization["iv"] =  iv
  jwe_complete_serialization["cyphertext"] =  cyphertext
  jwe_complete_serialization["tag"] =  authentication_tag
  jwe_complete_serialization["recipients"] =  []

  recipient = {}

  header = {}
  if(len(enc)):
    header['enc'] = enc
  if(len(x5c)):
    header['x5c'] = x5c
  if(len(header)):
    recipient["header"] = header

  recipient["encrypted_key"] = content_encrypted_key
  jwe_complete_serialization["recipients"].append(recipient)

  return(jwe_complete_serialization)

def jwe_complete_serialization_to_compact_token(jwe_complete_serialization : dict) -> str:

  jwe_vector = []
  jwe_vector.append(jwe_complete_serialization["protected"])
  jwe_vector.append(jwe_complete_serialization["recipients"][0]["encrypted_key"])
  jwe_vector.append(jwe_complete_serialization["iv"])
  jwe_vector.append(jwe_complete_serialization["cyphertext"])
  jwe_vector.append(jwe_complete_serialization["tag"])

  jwe_compact_token = ".".join(jwe_vector)

  return(jwe_compact_token)

def test_encrypt(two_party_tel_vcon : vcon.Vcon) -> None:
  plaintext = two_party_tel_vcon.dumps()

  symmetric_key = jose.utils.base64url_encode(secrets.token_bytes(nbytes=int(256/8))).decode("utf-8")
  print("sym key: {}".format(symmetric_key))

  content_key = {}
  content_key["kty"] = "oct"
  content_key["k"] = symmetric_key
  content_key["enc"] = "A256GCM"

  jwe_content_token = jose.jwe.encrypt(plaintext,
    jose.utils.base64url_decode(bytes(content_key["k"], "utf-8")),
    encryption=content_key['enc'],
    algorithm="dir",
    cty="application/vcon").decode('utf-8')
  print("token: {}".format(jwe_content_token))
  (protected, content_encrypted_key, iv, cyphertext, authentication_tag) = jwe_content_token.split('.')
  print("protected: {}".format(jose.utils.base64url_decode(bytes(protected, 'utf-8'))))
  print("content enc key: {}".format(content_encrypted_key))


  decrypt_content_token = ".".join([protected, "", iv, cyphertext, authentication_tag])
  print("decrypt token: {}".format(decrypt_content_token))

  decrypted_plaintext = jose.jwe.decrypt(decrypt_content_token,
    jose.utils.base64url_decode(bytes(content_key["k"], "utf-8")))
  assert(decrypted_plaintext.decode("utf-8") == plaintext)

  if(0):
    encryption = "A256GCM"
    algorithm = "dir"
    key = "mysecret123456789012345678901234"

  keys = [ {"kty":"RSA",
            "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw",
            "e":"AQAB",
            "alg":"RS256",
            "kid":"2011-04-29"}]
  # both of these work
  #encryption = "A256GCM"
  encryption = "A256CBC-HS512"

  encryption_key = build_encryption_jwk_from_pem_file(DIVISION_CERT)
  print("encryption_key: {}".format(json.dumps(encryption_key, indent=2)))

  # Either of these work
  #algorithm = "RSA-OAEP"
  #algorithm = "RSA1_5"

  # Cannot seem to get 128, 192 or 256 A*KW working
  #algorithm = "A192KW"

  #jwe_key = jose.jwk.construct(keys[0], algorithm)
  jwe_token = jose.jwe.encrypt(plaintext, encryption_key, encryption, encryption_key['alg']).decode('utf-8')
  print("token: {}".format(jwe_token))
  (header, encrypted_key, recip_iv, recip_cyphertext, recip_authentication_tag) = jwe_token.split('.')

  print("header: {}".format(jose.utils.base64url_decode(bytes(header, 'utf-8'))))
  print("encrypted_key: {}".format(encrypted_key))
  print("iv: {}".format(recip_iv))
  print("cyphertext: {}".format(recip_cyphertext))
  print("authentication_tag: {}".format(recip_authentication_tag))

  jwe_serialization = {}
  jwe_serialization["protected"] = protected
  jwe_serialization["iv"] =  iv
  jwe_serialization["cyphertext"] =  cyphertext
  jwe_serialization["tag"] =  authentication_tag
  jwe_serialization["recipients"] =  []

  recipient = {}
  recipient["header"] = json.loads(jose.utils.base64url_decode(bytes(header, 'utf-8')).decode('utf-8'))
  recipient["encrypted_key"] = encrypted_key
  jwe_serialization["recipients"].append(recipient)

  #print("JWE: {}".format(jwe_serialization))
  print("JWE: {}".format(json.dumps(jwe_serialization, indent=2)))


def test_x5c_encrypt(two_party_tel_vcon : vcon.Vcon) -> None:
  plaintext = two_party_tel_vcon.dumps()

  encryption_key = build_encryption_jwk_from_pem_file(DIVISION_CERT)
  print("encryption_key: {}".format(json.dumps(encryption_key, indent=2)))

  # both of these work
  #encryption = "A256GCM"
  encryption = "A256CBC-HS512"

  jwe_compact_token = jose.jwe.encrypt(plaintext, encryption_key, encryption, encryption_key['alg']).decode('utf-8')

  jwe_complete_serialization = jwe_compact_token_to_complete_serialization(jwe_compact_token, enc = encryption, x5c = [])
  print("JWE complete serialization: {}".format(json.dumps(jwe_complete_serialization, indent=2)))

  jwe_compact_token_reconstructed = jwe_complete_serialization_to_compact_token(jwe_complete_serialization)

  assert(jwe_compact_token == jwe_compact_token_reconstructed)

  (header, signing_key) = vcon.security.build_signing_jwk_from_pem_files(DIVISION_PRIVATE_KEY, [DIVISION_CERT])
  signing_key['alg'] = encryption_key['alg']

  plaintext_decrypted = jose.jwe.decrypt(jwe_compact_token_reconstructed, signing_key).decode('utf-8')

  assert(plaintext == plaintext_decrypted)



