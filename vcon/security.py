
import os
import typing
import cryptography.hazmat.backends.openssl.backend
import cryptography.x509
#import re
import base64
import jose
import datetime
import hsslms
import hashlib


# =============================== JWS, JWK Helper Functions ===========================
#              JOSE JSON Web Key and JSON Web Signature RFC7515, RFC7517

class InvalidCertDate(Exception):
  """ Cert not_valid_before or not_valid_after dates don't include today """

def load_string_from_file(file_name : str):
  file_contents_string = None
  with open(file_name, 'r') as file_handle:
    file_contents_string = file_handle.read()

  return(file_contents_string)

def load_pem_cert(cert_file : str) -> typing.Tuple[cryptography.x509.Certificate, str]:
  """
  Load PEM formate certificate containing public key and construct cert object and DER representation of PEM file.

  Returns:
    Tuple(cert_object, str): cert object and DER string
  """
  cert_string = load_string_from_file(cert_file)

  # Need the base64 encoded cert with no header, footer or white space for the x5c field in the key
  #bytes_start = cert_string.find('-\n') + 1
  #bytes_end = cert_string.find('\n-', bytes_start)
  #print("PEM header end: {} foot start: {}".format(bytes_start, bytes_end))
  # Pulls only the first encoded PEM object in the string
  #cert_no_begin_end = cert_string[bytes_start : bytes_end]

  # basically the DER format of the PEM cert
  #cert_no_whitespace = re.sub(r"\s", "", cert_no_begin_end)
  #print(cert_no_whitespace)

  # Import in PEM format
  cert_object = cryptography.x509.load_pem_x509_certificate(bytes(cert_string, 'utf-8'), cryptography.hazmat.backends.openssl.backend)
  # Alternatively load DER form:
  #cert_object = cryptography.x509.load_der_x509_certificate(base64.b64decode(div_cert_no_whitespace), cryptography.hazmat.backends.openssl.backend)
  der = base64.b64encode(cert_object.public_bytes(cryptography.hazmat.primitives.serialization.Encoding.DER)).decode('utf-8')
  #, cryptography.hazmat.primitives.serialization.PublicFormat.SubjectPublicKeyInfo)
  #print("DER: {}".format(der))
  #assert(der == cert_no_whitespace)

  return(cert_object, der)

def load_x5c_from_pem_certs(cert_pem_file_names : typing.List[str]) -> typing.List[str]:
  """
  Construct a x5c compatible list (RFC7515,RFC7517,RFC7518) from certifcate PEM files.

  Parameters:
    cert_pem_file_names (List[str]): list of PEM file names representing the certificate chain
             sorted in order from the signing cert for the JWS/JWE to the certificate authority
             root of the chain.

  Returns:
    List(str): The certifcate chain in DER format campatible with the c5c parameter in the
             above reference RFCs.

  """

  c5x_list = []
  for file_name in cert_pem_file_names:
    der_string = load_pem_cert(file_name)[1]
    c5x_list.append(der_string)

  return(c5x_list)

def der_to_certs(x5c : typing.List[str]) -> typing.List[cryptography.x509.Certificate]:
  """
  Construct the cryptograpy certifate objects for the list of DER format certificate strings

  Parameters:
    x5c (List[str]): list containing DER foramt cert strings (e.g. RFC7517)

  Returns:
    List of certificate object for each DER passed in.
  """
  cert_list = []
  for der in x5c:
    cert_object = cryptography.x509.load_der_x509_certificate(base64.b64decode(der), cryptography.hazmat.backends.openssl.backend)
    cert_list.append(cert_object)

  return(cert_list)

def load_pem_key(key_file_name : str) -> cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey:
  """
  Load PEM format private key and construct private key object

  Returns:
    Tuple(cert_object, str): cert object and DER string
  """
  pem_key_string = load_string_from_file(key_file_name)

  # cryptography.x509.load_pem_x509_private_key does not exist.  So we much wade through hazmat
  private_key_object = cryptography.hazmat.primitives.serialization.load_pem_private_key(bytes(pem_key_string, 'utf-8'), None, backend=None)
  #print("private_key type: {}".format(type(private_key_object)))
  #print("private dir {}".format(dir(private_key_object.private_numbers())))

  return(private_key_object)

def build_signing_jwk_from_pem_files(private_key_pem_file_name : str, cert_chain_pem_file_names : typing.List[str]) -> typing.Tuple[dict, dict]:
  """
  Read PEM files for pricate key and certificate chain all in PEM format and construct header and JWK for signing

  Parameters:
    private_key_pem_file_name (str): the private key to use for signing the vcon.

    cert_chain_pem_file_names (List{str]): file names for the pem format certicate chain for the
      private key to use for signing.  The cert/public key corresponding to the private key should be the
      first cert.  THe certificate authority root should be the last cert.

  Returns:
    Tuple[dict, dict]: header, JWK
        - header appropriate for including in JWS including x5c and alg
        - JWK including private key info for signing a JWS

  """
  # Load the cert chain into a x5c compatible array
  x5c = load_x5c_from_pem_certs(cert_chain_pem_file_names)

  algorithm = "RS256"

  header = {}
  header['x5c'] = x5c
  header["alg"] = algorithm

  private_key_object = load_pem_key(private_key_pem_file_name)

  # Only need the public key/object for the first/signing cert
  cert_object = der_to_certs([x5c[0]])[0]

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

  return(header, signing_key)

def verify_cert_chain(cert_chain : typing.List[cryptography.x509.Certificate]) -> None:
  """
  Verify the chain of certs validate the preseeding cert in the list and that the dates are valid.

  Parameters:
    cert_chain (Certicate): the following cert should be the issuer for the preceding cert

  Raises invalid cert or date as found.
  """

  # TODO: The certificate and certificate chain verification needs a whole lot more
  #       scrutany and unit testing.  Should Get 100% coverage.

  if(len(cert_chain) < 2):
    raise AttributeError("No CA. Cert chain must contain at least 2 certs")

  # TODO: should the root CA be used to verify itself???

  for index, issuer_cert in enumerate(cert_chain):
    # Skip the first cert, its the cert used for signing or encryption.
    # Its not an issuer.
    if(index > 0):
      #print("verifying cert: {}".format(index - 1))
      verify_cert(cert_to_verify, issuer_cert)

    cert_to_verify = issuer_cert

def verify_cert(cert_to_verify : cryptography.x509.Certificate, issuer_cert : cryptography.x509.Certificate) -> None:
  """
  Verify the signature of the given cert matches that of the issuer cert.

  Parameters:
    cert_to_verify (Certifcate): cert on which to verify the signature and dates
    issuer_cert (Certifcate): cert which should be the signer/issuer of the cert_to_verify

  Raises exceptions for invalid signature or date on the cert to verify.
  """
  issuer_cert.public_key().verify(
    cert_to_verify.signature,
    cert_to_verify.tbs_certificate_bytes,
    cryptography.hazmat.primitives.asymmetric.padding.PKCS1v15(),
    cert_to_verify.signature_hash_algorithm)

  # check dates on certs
  now = datetime.datetime.today()

  if(now < cert_to_verify.not_valid_before):
    name = "None"
    alt_name = "None"
    try:
      name = cert_to_verify.subject.get_attributes_for_oid(cryptography.x509.NameOID.COMMON_NAME)[0].value
      alt_name = cert_to_verify.subject.get_attributes_for_oid(cryptography.x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)[0].value
    except Exception as e:
      # REMOVE THIS RAISE after testing
      raise e

    raise InvalidCertDate("certificate with name: {} altname: {} is not valid until: {}".format(
      name, alt_name,
      cert_to_verify.not_valid_before))

  if(now > cert_to_verify.not_valid_after):
    name = "None"
    alt_name = "None"
    try:
      name = cert_to_verify.subject.get_attributes_for_oid(cryptography.x509.NameOID.COMMON_NAME)[0].value
      alt_name = cert_to_verify.subject.get_attributes_for_oid(cryptography.x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)[0].value
    except Exception as e:
      # REMOVE THIS RAISE after testing
      raise e

    raise InvalidCertDate("certificate with name: {} altname: {} is not valid after: {}".format(
      name, alt_name,
      cert_to_verify.not_valid_before))

  # TODO need to check revokations as well

# =============================== JOSE JWE Helper Functions ===========================

def build_encryption_jwk_from_pem_file(cert_pem_file_name : str) -> dict:

  pem_string = load_string_from_file(cert_pem_file_name)

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

# =============================== SHA-512 Hash Helper Functions ===========================
#                            SHA-512 Hash (RFC6234)

def sha_512_hash(data : bytes) -> str:
  """
  Generate the SHA-512 hash for the single chunk data pased in.

  Parameters:
    data - binary bytes for which to generate the hash

  Returns:
    base64 URL encoded SHA-512 hash of bytes argument

  """

  hasher = hashlib.sha512()

  hasher.update(data)

  sig_hash = jose.utils.base64url_encode(hasher.digest()).decode('utf-8')

  #print("sha_512_hash: {}".format(sig_hash))
  return(sig_hash)

# =============================== One Time Signature Helper Functions ===========================
#                            Leighton-Micali One Time Signature (RFC8554)

def lm_one_time_signature(data : bytes) -> typing.Tuple[str, str]:
  """
  Sign data bytes using Leighton-Micali One Time Signature (RFC8554) method

  Returns:
    Tuple(str, str): public key and signature strings
  """
  one_time_private_key = hsslms.LM_OTS_Priv(
    hsslms.LMOTS_ALGORITHM_TYPE.LMOTS_SHA256_N32_W8, os.urandom(16), 0, os.urandom(32))

  signature = jose.utils.base64url_encode(one_time_private_key.sign(data)).decode('utf-8')

  public_key = jose.utils.base64url_encode(one_time_private_key.gen_pub().pubkey).decode('utf-8')

  #print("public_key: {}".format(public_key))
  #print("sig: {}".format(signature))

  return(public_key, signature)

def verify_lm_one_time_signature(data : bytes, signature : str, public_key : str) -> None:
  """
  Verify data bytes with signature and key using Leighton-Micali One Time Signature (RFC8554) method

  Raises: exceptions if the signature fails to verify
  """
  public_key_bytes = jose.utils.base64url_decode(bytes(public_key, 'utf-8'))

  public_key_object = hsslms.LM_OTS_Pub(public_key_bytes)

  signature_bytes = jose.utils.base64url_decode(bytes(signature, 'utf-8'))

  public_key_object.verify(data, signature_bytes)

