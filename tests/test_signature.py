""" unit test related to RFC7515 JSON Web Signature (JWS) functionality """

import typing
import pytest
import vcon
import vcon.security
import json
import pprint
import cryptography.x509
import base64

import jose.jwk
import jose.jws
import datetime

CA_CERT = "certs/fake_ca_root.crt"
CA2_CERT = "certs/fake_ca2_root.crt"
EXPIRED_CERT = "certs/expired_div.crt"
DIVISION_CERT = "certs/fake_div.crt"
DIVISION_PRIVATE_KEY = "certs/fake_div.key"
GROUP_CERT = "certs/fake_grp.crt"
GROUP_PRIVATE_KEY = "certs/fake_grp.key"

call_data = {
      "epoch" : "1652552179",
      "destination" : "2117",
      "source" : "+19144345359",
      "rfc2822" : "Sat, 14 May 2022 18:16:19 -0000",
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
  first_party = vCon.set_party_parameter("tel", call_data['source'])
  second_party = vCon.set_party_parameter("tel", call_data['destination'])
  return(vCon)

@pytest.fixture()
def ca_cert() -> typing.Tuple[cryptography.x509.Certificate, str]:
  """ load certificate of authority (issuer of Division cert) X.509 certificate and public key from file and return the string """
  return(vcon.security.load_pem_cert(CA_CERT))

@pytest.fixture()
def ca2_cert() -> typing.Tuple[cryptography.x509.Certificate, str]:
  """ load certificate of 2nd authority (issuer of Division cert) X.509 certificate and public key from file and return the string """
  return(vcon.security.load_pem_cert(CA2_CERT))

@pytest.fixture()
def div_cert() -> typing.Tuple[cryptography.x509.Certificate, str]:
  """ load Division X.509 certificate and public key from file and return the string """
  return(vcon.security.load_pem_cert(DIVISION_CERT))

@pytest.fixture()
def expired_cert() -> typing.Tuple[cryptography.x509.Certificate, str]:
  """ load expired Division X.509 certificate and public key from file and return the string """
  return(vcon.security.load_pem_cert(EXPIRED_CERT))

@pytest.fixture()
def div_key() -> cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey:
  """ load Division X.509 private key from file and return the string """
  key_object = vcon.security.load_pem_key(DIVISION_PRIVATE_KEY)

  return(key_object)

@pytest.fixture()
def good_x5c_list() -> typing.List[str]:
  file_names = [GROUP_CERT, DIVISION_CERT, CA_CERT]
  c5x = vcon.security.load_x5c_from_pem_certs(file_names)
  return(c5x)

@pytest.fixture()
def invalid_x5c_list() -> typing.List[str]:
  file_names = [GROUP_CERT, EXPIRED_CERT, CA_CERT]
  c5x = vcon.security.load_x5c_from_pem_certs(file_names)
  return(c5x)

# Not sure this interface is right or needed
def build_verification_jwk_from_file(cert_chain_der_strings : typing.List[str], ca_pem_strings : typing.List[str]) -> dict:
   """
   Read DER strings for certificate chain and construct a JWS for signed verification.
   Verify the cert chain is linked to one of the certficate authorites in the list provided.

   Returns:
     JWK (dict): key for JWS verification of signed JWS
   """

def test_key(div_cert: typing.Tuple[cryptography.x509.Certificate, str], div_key: cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey) -> None:

  cert_object = div_cert[0]
  print("cert_object type: {}".format(type(cert_object)))
  cert_der = div_cert[1]
  print(cert_der)

  private_key_object = div_key
  # cert_object is a cryptography.x509.Certificate??
  print("cert_object type: {}".format(type(cert_object)))
  print("cert_object dir: {}".format(dir(cert_object.public_key())))
  print("cert_object valid start: {}".format(cert_object.not_valid_before))
  print("cert_object valid end: {}".format(cert_object.not_valid_after))
  print("cert_object pub nums dir: {}".format(dir(cert_object.public_key().public_numbers())))
  print("cert_object pub key dir: {}".format((cert_object.public_key().public_numbers().public_key)))
  print("cert_object n: {}".format(jose.utils.base64url_encode(jose.utils.long_to_bytes(cert_object.public_key().public_numbers().n))))
  print("cert_object e: {}".format(jose.utils.base64url_encode(jose.utils.long_to_bytes(cert_object.public_key().public_numbers().e))))
  #print("cert_object dir: {}".format(dir(cert_object)))
  #print("cert_object issuer: {}".format(cert_object.issuer.rfc4514_string()))
  #print("cert_object subject: {}".format(cert_object.subject.rfc4514_string()))

  # subject is a cryptography.x509.name.Name
  # field is a cryptography.x509.name.NameAttribute
  for field in cert_object.subject:
    #print(dir(field.oid))
    print("subject {:20} {:20} {:22} {}".format(field.rfc4514_attribute_name, field.oid.dotted_string, field.oid._name, field.value))
    #         RFC4514 Name         ASN.1 OID            OID Name               Example Value
    # subject C                    2.5.4.6              countryName            US
    # subject ST                   2.5.4.8              stateOrProvinceName    MA
    # subject L                    2.5.4.7              localityName           Faketown
    # subject O                    2.5.4.10             organizationName       FakeVcon
    # subject OU                   2.5.4.11             organizationalUnitName Division
    # subject CN                   2.5.4.3              commonName             div.fakevcon.io
    # subject 1.2.840.113549.1.9.1 1.2.840.113549.1.9.1 emailAddress           admin@fakevcon.org
    # subject 2.5.29.17            2.5.29.17            subjectAltName         div.fakevcon.org

  for field in cert_object.issuer:
    print("issuer {:20} {:20} {:22} {}".format(field.rfc4514_attribute_name, field.oid.dotted_string, field.oid._name, field.value))

  algorithm = "RS256"
  #crypt_key = jose.jwk.construct(cert_object.public_key(), algorithm)

  #print(crypt_key)
  #print(dir(crypt_key))

  signing_key = {}
  signing_key["kty"] = "RSA"
  signing_key["use"] = "sig"
  signing_key["alg"] = algorithm
  signing_key["n"] = jose.utils.base64url_encode(jose.utils.long_to_bytes(cert_object.public_key().public_numbers().n)).decode('utf-8')
  signing_key["e"] = jose.utils.base64url_encode(jose.utils.long_to_bytes(cert_object.public_key().public_numbers().e)).decode('utf-8')
  signing_key["d"] = jose.utils.base64url_encode(jose.utils.long_to_bytes(private_key_object.private_numbers().d)).decode('utf-8')

  # if missing, can be computed using:
  # (p,p) = cryptography.hazmat.primitives.asymmetric.rsa.rsa_recover_prime_factors(n, e, d)
  signing_key["p"] = jose.utils.base64url_encode(jose.utils.long_to_bytes(private_key_object.private_numbers().p)).decode('utf-8')
  signing_key["q"] = jose.utils.base64url_encode(jose.utils.long_to_bytes(private_key_object.private_numbers().q)).decode('utf-8')

  # if missing, can be computed using:
  # cryptography.hazmat.primitives.asymmetric.rsa.rsa_crt_dmp1(d, p)
  signing_key["dp"] = jose.utils.base64url_encode(jose.utils.long_to_bytes(private_key_object.private_numbers().dmp1)).decode('utf-8')

  # if missing, can be computed using:
  # cryptography.hazmat.primitives.asymmetric.rsa.rsa_crt_dmq1(d, q)
  signing_key["dq"] = jose.utils.base64url_encode(jose.utils.long_to_bytes(private_key_object.private_numbers().dmq1)).decode('utf-8')

  # if missing, can be computed using:
  # cryptography.hazmat.primitives.asymmetric.rsa.rsa_crt_iqmp(p,q)
  signing_key["qi"] = jose.utils.base64url_encode(jose.utils.long_to_bytes(private_key_object.private_numbers().iqmp)).decode('utf-8')

  print("signing key:")
  pprint.pprint(signing_key)

  verification_key = {}
  verification_key["kty"] = "RSA"
  verification_key["use"] = "sig"
  verification_key["alg"] = algorithm
  verification_key["n"] = jose.utils.base64url_encode(jose.utils.long_to_bytes(cert_object.public_key().public_numbers().n)).decode('utf-8')
  verification_key["e"] = jose.utils.base64url_encode(jose.utils.long_to_bytes(cert_object.public_key().public_numbers().e)).decode('utf-8')
  #jwk["e"] = "AQAB"

  header = {}
  header["x5c"] = [ cert_der ]
  print("\nverification key:")
  pprint.pprint(verification_key)

  #x5c_key = jose.jwk.construct(jwk, algorithm=algorithm)
  payload = { "mything" : "data to sign"}
  #jws_token = x5c_key.sign(payload)
  jws_token = jose.jws.sign(payload, signing_key, algorithm=signing_key["alg"])

  print(jws_token)

  verification_key["n"] = jose.utils.base64url_encode(jose.utils.long_to_bytes(cert_object.public_key().public_numbers().n)).decode('utf-8')
  verified_payload = jose.jws.verify(jws_token, verification_key, algorithm)
  print("verified: {}".format(verified_payload))

def test_verify_cert(div_cert : typing.Tuple[cryptography.x509.Certificate, str],
  ca_cert : typing.Tuple[cryptography.x509.Certificate, str]) -> None:
  cert_to_verify, cert_der =  div_cert
  issuer_cert, issuer_der = ca_cert

  vcon.security.verify_cert(cert_to_verify, issuer_cert)

def test_verify_expired_cert(expired_cert : typing.Tuple[cryptography.x509.Certificate, str],
  ca_cert : typing.Tuple[cryptography.x509.Certificate, str]) -> None:
  cert_to_verify, cert_der =  expired_cert
  issuer_cert, issuer_der = ca_cert

  try:
    vcon.security.verify_cert(cert_to_verify, issuer_cert)
    raise Exception("Should have thrown  exception for expired cert")

  except vcon.security.InvalidCertDate as invalid_date_e:
    pass

def test_verify_ca_ca(ca_cert : typing.Tuple[cryptography.x509.Certificate, str]) -> None:
  """ ca is self signed, so technically it can be used to verify itself """
  ca1_cert = ca_cert[0]
  ca2_cert = ca_cert[0]

  vcon.security.verify_cert(ca1_cert, ca2_cert)

def test_verify_wrong_cert(div_cert : typing.Tuple[cryptography.x509.Certificate, str],
  ca2_cert : typing.Tuple[cryptography.x509.Certificate, str]) -> None:
  cert_to_verify, cert_der =  div_cert
  issuer_cert, issuer_der = ca2_cert

  try:
    vcon.security.verify_cert(cert_to_verify, issuer_cert)
    raise Exception("Should have thrown  exception for invalid signature")

  except cryptography.exceptions.InvalidSignature as invalid_sig:
    # Should get her because this CA did not sign the cert being verified
    pass

def test_cert_chain(good_x5c_list : typing.List[str]) -> None:
  c5x_list = good_x5c_list
  cert_chain = vcon.security.der_to_certs(c5x_list)

  vcon.security.verify_cert_chain(cert_chain)

def test_invalid_cert_chain(invalid_x5c_list : typing.List[str]) -> None:
  c5x_list = invalid_x5c_list
  cert_chain = vcon.security.der_to_certs(c5x_list)

  try:
    vcon.security.verify_cert_chain(cert_chain)
    raise Exception("SHould have caught invalid cert at element 1 in chain")

  # Should raise this exception:
  except cryptography.exceptions.InvalidSignature as invalid_error:
    pass

def test_expired_cert_chain(expired_cert : typing.Tuple[cryptography.x509.Certificate, str], ca_cert : typing.Tuple[cryptography.x509.Certificate, str]) -> None:
  c5x_list = [expired_cert[1], ca_cert[1]]
  cert_chain = vcon.security.der_to_certs(c5x_list)

  try:
    vcon.security.verify_cert_chain(cert_chain)
    raise Exception("Should have raise exceptin for invalid date on cert in element 0 of chain")

  # Should raise this exception:
  except vcon.security.InvalidCertDate as invalid_error:
    pass

def test_sign_vcon(two_party_tel_vcon : vcon.Vcon) -> None:
  try:
    two_party_tel_vcon.sign(GROUP_PRIVATE_KEY, [GROUP_CERT, DIVISION_CERT, CA_CERT])
    raise Exception("Expected exception as sign was attempted with UUID not set.")

  except vcon.InvalidVconState as e:
    pass

  two_party_tel_vcon.set_uuid("vcon.dev")
  uuid = two_party_tel_vcon.uuid
  # Now this should work as we have set a UUID
  two_party_tel_vcon.sign(GROUP_PRIVATE_KEY, [GROUP_CERT, DIVISION_CERT, CA_CERT])

  # Should still be valid to read UUID
  assert(uuid == two_party_tel_vcon.uuid)

  try:
    two_party_tel_vcon.sign(GROUP_PRIVATE_KEY, [GROUP_CERT, DIVISION_CERT, CA_CERT])
    raise Exception("Should have thrown an exception as this vcon was already signed")

  except vcon.InvalidVconState as already_signed_error:
    if(already_signed_error.args[0].find("should") != -1):
      raise already_signed_error

  try:
    two_party_tel_vcon.verify([CA_CERT])
    raise Exception("Should have thrown an exception as this vcon was signed locally")

  except vcon.InvalidVconState as locally_signed_error:
    # Expected to get here because vCon was signed locally
    # Its already verified
    if(locally_signed_error.args[0].find("should") != -1):
      raise locally_signed_error

  vcon_json = two_party_tel_vcon.dumps()
  #print("Signed vcon: {}".format(vcon_json))

  deserialized_signed_vcon = vcon.Vcon()
  deserialized_signed_vcon.loads(vcon_json)

  try:
    duuid = deserialized_signed_vcon.uuid
    raise Exception("Should be an exception thrown here as vCon is signed, but not verified")

  except vcon.UnverifiedVcon as e:
    pass

  vcon_json2 = deserialized_signed_vcon.dumps()
  assert(vcon_json == vcon_json2)

  try:
    party_count = len(deserialized_signed_vcon.parties)
    raise Exception("Should not get here.  Vcon is signed, but not yet verified.  Cannot access data.")

  except vcon.UnverifiedVcon as unverified_error:
    # Should get here
    pass

  deserialized_signed_vcon.verify([CA_CERT])
  assert(len(deserialized_signed_vcon.parties) == 2)
  assert(deserialized_signed_vcon.parties[0]['tel'] == call_data['source'])
  assert(deserialized_signed_vcon.parties[1]['tel'] == call_data['destination'])
  assert(uuid == deserialized_signed_vcon.uuid)
