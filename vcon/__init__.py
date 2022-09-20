"""
Module for creating and modifying vCon conversation containers.
see https:/vcon.dev
"""
import typing
import vcon.utils
import vcon.security
import json
import jose.utils
import jose.jws
import jose.jwe
import enum
import sys
import uuid6
import time
import hashlib

_last_v8_timestamp = None

class VconStates(enum.Enum):
  """ Vcon states WRT signing and verification """
  UNKNOWN = 0
  UNSIGNED = 1
  SIGNED = 2
  UNVERIFIED = 3
  VERIFIED = 4
  ENCRYPTED = 5
  DECRYPTED = 6


class UnsupportedVconVersion(Exception):
  """ Thrown if vcon version string is not of set of versions supported by this package"""

class UnverifiedVcon(Exception):
  """ Payload is signed, but not verified.  Must be verified before reading data """

class InvalidVconState(Exception):
  """ Vcon is in an invalid state for a given operation """

class InvalidVconJson(Exception):
  """ JSON not valid for Vcon """

class InvalidVconHash(Exception):
  """ Hash does not match the content/body """

class VconDictList:
  """ descriptor for Lists of dicts in vcon """
  def __set_name__(self, owner_class, name):
    #print("defining new VconList: {}".format(name))
    self.name = name

  def __get__(self, instance_object, class_type = None) -> list:
    #print("getting: {} inst type: {} class type: {}".format(self.name, type(instance_object), type(class_type)))
    # TODO: once signed, this should return a read only list

    if(instance_object._state == VconStates.UNVERIFIED):
      raise UnverifiedVcon("vCon is signed, but not verified. Call verify before reading data.")

    return(instance_object._vcon_dict.get(self.name, None))

  def __set__(self, instance_object, value : dict) -> None:
    raise AttributeError("not allowed to replace {} List".format(self.name))

class Vcon():
  """
  Constructor, Serializer and Deserializer for vCon conversation data container.

  Attributes:
    parties (List[dict]): containing information on each party to the conversation
    dialog (List[dict]): containing information dialog exchanges (text or audio/video recordings)
    analysis (List[dict]): containing analysis information on the dialog
    attachments (List[dict]): containing meta data about as well as the documents exchanged during the conversation

  """

  # Some commonly used MIME types for convenience
  MIMETYPE_WAV = "audio/x-wav"

  # Dict keys
  VCON_VERSION = "vcon"
  UUID = "uuid"
  PARTIES = "parties"
  DIALOG = "dialog"
  ANALYSIS = "analysis"
  ATTACHMENTS = "attachments"

  parties = VconDictList()
  dialog = VconDictList()
  analysis = VconDictList()
  attachments = VconDictList()

  # TODO:  work out states the vcon can be in.  For example:
  """
    unsigned
    signed
    signed_unverified
    signed_verified
    encrypted
    encrypted_unverified
    decryppted_verified

  Also are there failure cases for the above?

  JSW (RFC7515) signing stored in:
  _jsw_dict
  {
    payload
    signatures
    [
      {
        protected
        header
        signature
      } [, ...]
    ]
  }


  """

  def __init__(self):
    self._state = VconStates.UNSIGNED
    self._jws_dict = None
    self._jwe_dict = None

    self._vcon_dict = {}
    self._vcon_dict[Vcon.VCON_VERSION] = "0.0.1"
    self._vcon_dict[Vcon.PARTIES] = []
    self._vcon_dict[Vcon.DIALOG] = []
    self._vcon_dict[Vcon.ANALYSIS] = []
    self._vcon_dict[Vcon.ATTACHMENTS] = []

  def __add_new_party(self, index : int) -> int:
    """
    check if a new party needs to be added to the list

    Parameters:
    index (int): -1 indicates adding a new party, positive numbers
          throw AttributeError if the party with that index does not already exist

    Returns:
      party index in the list
    """
    party = index
    if(party == -1):
      self._vcon_dict[Vcon.PARTIES].append({})
      party = len(self._vcon_dict[Vcon.PARTIES]) - 1

    else:
      if(not len(self._vcon_dict[Vcon.PARTIES]) > index):
        raise AttributeError(
          "index: {} > then party List length: {}.  Use index of -1 to add one to the end.".format(
          index, len(self._vcon_dict[Vcon.PARTIES])))

    return(party)

  def get_conversation_time(self) -> typing.Tuple[str, float]:
    """
    Get the start time and duration of the vcon

    Parameters: none

    Returns:
      Tuple(str, float): RFC2822 format string start time and float duration in seconds
    """
    # TODO: loop through dialogs and find the oldest start time, calculate end time from
    # duration, find the most recent end time and return the results

    # TODO: Dialog recordings for mutiple parties will not show the start/join time for
    # all of the parties, only the first to join.  Requires analysis of recording to show
    # when party speaks, but this may not be a good indicator of join time.  Where as signalling
    # has defininte joine time for each party, but is not captured in the vcon.
    raise Exception("not implemented")

  def set_party_tel_url(self, tel_url : str, party_index : int =-1) -> int:
    """
    Set tel URL for a party.

    Parameters:
    tel_url
    party_index (int): index of party to set tel url on
                  (-1 indicates a new party should be added)

    Returns:
    int: if success, opsitive int index of party in list
    """

    # TODO: should label as caller or called

    party_index = self.__add_new_party(party_index)

    self._vcon_dict[Vcon.PARTIES][party_index]['tel'] = tel_url

    return(party_index)

  def add_dialog_inline_recording(self, body : bytes,
    start_time : typing.Union[str, int, float],
    duration : typing.Union[int, float],
    parties : typing.Union[int, typing.List[int], typing.List[typing.List[int]]],
    mime_type : str,
    file_name : str = None) -> int:
    """
    Add a recording of a portion of the conversation, inline (base64 encoded) to the dialog.

    Parameters:
    body (bytes): bytes for the audio or video recording (e.g. wave or MP3 file).
    start_time (str, int, float): Date, time of the start of the recording.
               string containing RFC 2822 or RFC3339 date time stamp or int/float
               containing epoch time (since 1970) in seconds.
    duration (int or float): duration of the recording in seconds
    parties (int, List[int], List[List[int]]): party indices speaking in each
               channel of the recording.
    mime_type (str): mime type of the recording
    file_name (str): file name of the recording (optional)

    Returns:
            Number of bytes read from body.
    """
    # TODO: do we want to know the number of channels?  e.g. to verify party list length

    # TODO: should we validate the start time?

    new_dialog = {}
    new_dialog['type'] = "recording"
    new_dialog['start'] = vcon.utils.cannonize_date(start_time)
    new_dialog['duration'] = duration
    new_dialog['parties'] = parties
    new_dialog['mimetype'] = mime_type
    if(file_name is not None):
      new_dialog['filename'] = file_name

    new_dialog['encoding'] = "base64url"
    encoded_body = jose.utils.base64url_encode(body).decode('utf-8')
    #print("encoded body type: {}".format(type(encoded_body)))
    new_dialog['body'] = encoded_body

    self._vcon_dict[Vcon.DIALOG].append(new_dialog)


    return(len(body))

  def decode_dialog_inline_recording(self, dialog_index : int) -> bytes:
    """
    Get the dialog recording at the given index, decoding it and returning the raw bytes.

    Parameters:
      dialog_index (int): index the the dialog in the dialog list, containing the inline recording

    Returns:
      (bytes): the bytes for the recording file
    """
    dialog = self.dialog[dialog_index]
    if(dialog["type"] != "recording"):
      raise AttributeError("dialog[{}] is not a recording file")
    if(dialog.get("body") is None):
      raise AttributeError("dialog[{}] does not contain an inline recording file")

    # This is wrong.  decode should take a string not bytes, but it fails without the bytes conversion
    # this is a bug in jose.baseurl_decode
    decoded_body = jose.utils.base64url_decode(bytes(dialog["body"], 'utf-8'))

    return(decoded_body)

  def add_dialog_external_recording(self, body : bytes,
    start_time : typing.Union[str, int, float],
    duration : typing.Union[int, float],
    parties : typing.Union[int, typing.List[int], typing.List[typing.List[int]]],
    external_url: str,
    mime_type : str = None,
    file_name : str = None,
    sign_type : str = "SHA-512") -> int:
    """
    Add a recording of a portion of the conversation, as a reference via the given
    URL, to the dialog and generate a signature and key for the content.  This
    method has the limitation that the entire recording must be passed in in-memory.

    Parameters:
    body (bytes): bytes for the audio or video recording (e.g. wave or MP3 file).
    start_time (str, int, float): Date, time of the start of the recording.
               string containing RFC 2822 or RFC 3339 date time stamp or int/float
               containing epoch time (since 1970) in seconds.
    duration (int or float): duration of the recording in seconds
    parties (int, List[int], List[List[int]]): party indices speaking in each
               channel of the recording.
    external_url (string): https URL where the body is stored securely
    mime_type (str): mime type of the recording (optional)
    file_name (str): file name of the recording (optional)
    sign_type (str): signature type to create for external signature
                     default= "SHA-512" use SHA 512 bit hash (RFC6234)
                     "LM-OTS" use Leighton-Micali One Time Signature (RFC8554

    Returns:
            Number of bytes read from body.
    """
    # TODO: need a streaming/chunk version of this so that we don't have to have the whole file in memory.

    new_dialog = {}
    new_dialog['type'] = "recording"
    new_dialog['start'] = vcon.utils.cannonize_date(start_time)
    new_dialog['duration'] = duration
    new_dialog['parties'] = parties
    new_dialog['url'] = external_url
    if(mime_type is not None):
      new_dialog['mimetype'] = mime_type
    if(file_name is not None):
      new_dialog['filename'] = file_name

    if(sign_type == "LM-OTS"):
      print("Warning: \"LM-OTS\" may be depricated", file=sys.stderr)
      key, signature = vcon.security.lm_one_time_signature(body)
      new_dialog['key'] = key
      new_dialog['signature'] = signature
      new_dialog['alg'] = "LMOTS_SHA256_N32_W8"

    elif(sign_type == "SHA-512"):
      sig_hash = vcon.security.sha_512_hash(body)
      new_dialog['signature'] = sig_hash
      new_dialog['alg'] = "SHA-512"

    else:
      raise AttributeError("Unsupported signature type: {}.  Please use \"SHA-512\" or \"LM-OTS\"".format(sign_type))

    self.dialog.append(new_dialog)

    return(len(body))


  def verify_dialog_external_recording(self, dialog_index : int, body : bytes) -> None:
    """
    Verify the given body of the externally stored recording for the indicted dialog.
    Using the signature and public key stored in the dialog, the content of the body
    of the recording is verifyed.

    Parameters:
      dialog_index (int): index of the dialog to be verified

      body (bytes): the contents of the recording which is stored external to this vCon

    Returns: none

    Raises exceptions if the signature and public key fail to verify the body.
    """

    dialog = self.dialog[dialog_index]

    if(dialog['type'] != "recording"):
      raise AttributeError("dialog[{}] is of type: {} not recording".format(dialog_index, dialog['type']))

    if(len(dialog['signature']) < 1 ):
      raise AttributeError("dialog[{}] signature: {} not set.  Must be for LMOTS_SHA256_N32_W8".format(dialog_index, dialog['signature']))

    if(dialog['alg'] == 'LMOTS_SHA256_N32_W8'):
      if(len(dialog['key']) < 1 ):
        raise AttributeError("dialog[{}] key: {} not set.  Must be for LMOTS_SHA256_N32_W8".format(dialog_index, dialog['key']))

      vcon.security.verify_lm_one_time_signature(body,
        dialog['signature'],
        dialog['key'])

    elif(dialog['alg'] == 'SHA-512'):
      sig_hash = vcon.security.sha_512_hash(body)
      if( dialog['signature'] != sig_hash):
        print("dialog[\"signature\"]: {} hash: {}".format(dialog['signature'], sig_hash))
        print("dialog: {}".format(json.dumps(dialog, indent=2)))
        raise InvalidVconHash("SHA-512 hash in signature does not match the given body for dialog[{}]".format(dialog_index))

    else:
      raise AttributeError("dialog[{}] alg: {} not supported.  Must be SHA-512 or LMOTS_SHA256_N32_W8".format(dialog_index, dialog['alg']))

  def add_analysis_transcript(self, dialog_index : int, transcript : dict, vendor : str, vendor_schema : str = None) -> None:
    """
    Add a transcript for the indicated dialog.

    Parameters:
    dialog_index (str): index to the dialog in the vCon dialog list that this trascript corresponds to.
    vendor (str): string token for the vendor of the audio to text transcription service
    vendor_schema (str): schema label for the transcription data.  Used to identify data format of the transcription
                  for vendors that have more than one format or version.
    """

    analysis_element = {}
    analysis_element["type"] = "transcript"
    # TODO should validate dialog_index??
    analysis_element["dialog"] = dialog_index
    analysis_element["body"] = transcript
    analysis_element["encoding"] = "json"
    analysis_element["vendor"] = vendor
    if(vendor_schema is not None):
      analysis_element["vendor_schema"] = vendor_schema

    self.analysis.append(analysis_element)

  def dumps(self, signed = True) -> str:
    """
    Dump the vCon as a JSON string.

    Parameters:

    signed (Boolean): If the vCon is signed locally or verfied,
        True: serialize the signed version
        False: serialize the unsigned version

    Returns:
             String containing JSON representation of the vCon.
    """

    # TODO: Should it throw an acception if its not signed?  Could have argument to
    # not throw if it not signed.

    if(self._state == VconStates.UNSIGNED):
      return(json.dumps(self._vcon_dict))

    if(self._state in [VconStates.SIGNED, VconStates.UNVERIFIED, VconStates.VERIFIED]):
      if(signed is False and self._state != VconStates.UNVERIFIED):
        return(json.dumps(self._vcon_dict))
      return(json.dumps(self._jws_dict))

    if(self._state in [VconStates.ENCRYPTED, VconStates.DECRYPTED]):
      if(signed is False):
        raise AttributeError("not supported: unsigned JSON output for encrypted vCon")
      return(json.dumps(self._jwe_dict))

    raise InvalidVconState("vCon state: {} is not valid for dumps".format(self._state))

  def loads(self, vcon_json : str) -> None:
    """
    Load the vCon from a JSON string.
    Assumes that this vCon is an empty vCon as it is not cleared.

    Decision as to what json form to be deserialized is:
    1) unsigned vcon must have a vcon and one or more of the following elements: parties, dialog, analysis, attachments
    2) JWS vCon must have a payload and signatures
    3) JWE vCon must have a cyphertext and recipients

    Parameters:
      vcon_json (str): string containing JSON representation of a vCon

    Returns: none
    """

    #TODO: Should check unsafe stuff is not loaded

    if(self._state != VconStates.UNSIGNED):
      raise InvalidVconState("Cannot load Vcon unless current state is UNSIGNED.  Current state: {}".format(self._state))

    vcon_dict = json.loads(vcon_json)

    # we need to check the format as to whether it is signed or
    # not and deconstruct the loaded object.
    # load differently based upon the contents of the JSON

    # Signed vCon (JWS)
    if(("payload" in vcon_dict) and
      ("signatures" in vcon_dict)
      ):
      self._vcon_dict = {}

      self._state = VconStates.UNVERIFIED
      self._jws_dict = vcon_dict

    # encrypted vCon (JWE)
    elif(("cyphertext" in vcon_dict) and
      ("recipients" in vcon_dict)
      ):
      self._vcon_dict = {}

      self._state = VconStates.ENCRYPTED
      self._jwe_dict = vcon_dict

    # Unsigned vCon has to have vcon version and
    elif(('vcon' in vcon_dict) and (
      # one of the following arrays
      ('parties' in vcon_dict) or
      ('dialog' in vcon_dict) or
      ('analysis' in vcon_dict) or
      ('attachments' in vcon_dict)
      )):

      # validate version
      version_string = vcon_dict.get('vcon', "not set")
      if(version_string != "0.0.1"):
        raise UnsupportedVconVersion("loads of JSON vcon version: \"{}\" not supported".format(version_string))

      self._vcon_dict = self.migrate_0_0_1_vcon(vcon_dict)

    # Unknown
    else:
      raise InvalidVconJson("Not recognized as a unsigned, signed or encrypted JSON vCon")


  def sign(self, private_key_pem_file_name : str, cert_chain_pem_file_names : typing.List[str]) -> None:
    """
    Sign the vcon using the given private key from the give certificate chain.

    Parameters:
      cert_chain_pem_file_names (List{str]): file names for the pem format certicate chain for the
        private key to use for signing.  The cert/public key corresponding to the private key should be the
        first cert.  THe certificate authority root should be the last cert.

    private_key_pem_file_name (str): the private key to use for signing the vcon.

    Returns: none
    """

    if(self._state == VconStates.SIGNED):
      raise InvalidVconState("Vcon was already signed.")

    if(self._state != VconStates.UNSIGNED):
      raise InvalidVconState("Vcon not in valid state to be signed: {}.".format(self._state))

    header, signing_jwk = vcon.security.build_signing_jwk_from_pem_files(private_key_pem_file_name, cert_chain_pem_file_names)

    # dot separated JWS token.  First part is the payload, second part is the signature (both base64url encoded)
    jws_token = jose.jws.sign(self._vcon_dict, signing_jwk, headers=header, algorithm=signing_jwk["alg"])
    #print(jws_token.split('.'))
    protected_header, payload, signature = jws_token.split('.')
    #print("decoded header: {}".format(jose.utils.base64url_decode(bytes(protected_header, 'utf-8'))))

    jws_serialization = {}
    jws_serialization['payload'] = payload
    jws_serialization['signatures'] = []
    first_sig = {}
    first_sig['header'] = header
    first_sig['signature'] = signature
    first_sig['protected'] = protected_header
    jws_serialization['signatures'].append(first_sig)

    self._jws_dict = jws_serialization
    self._state = VconStates.SIGNED

  def verify(self, ca_cert_pem_file_names : typing.List[str]) -> None:
    """
    Verify the signed vCon and its certificate chain which should be issued by one of the given CAs

    Parameters:
      ca_cert_pem_file_names (List[str]): list of Certificate Authority certificate PEM file names
        to verify the vCon's certificate chain.

    Returns: none

    Raises exceptions for invalid cert chaind, invalid cert dates or chain not issued by one
    of the given CAs.

    NOTE:  DOES NOT CHECK REVOKATION LISTS!!!
    """
    if(self._state == VconStates.SIGNED):
      raise InvalidVconState("Vcon was locally signed.  No need to verify")

    if(self._state == VconStates.VERIFIED):
      raise InvalidVconState("Vcon was already verified")

    if(self._state != VconStates.UNVERIFIED):
      raise InvalidVconState("Vcon cannot be verified invalid state: {}")

    if(self._jws_dict is None or
      ('signatures' not in self._jws_dict) or
      (len(self._jws_dict['signatures']) < 1) or
      ('signature' not in self._jws_dict['signatures'][0])
      ):
      raise InvalidVconState("Vcon JWS invalid")

    # Load an array of CA certficate objects to use to verify acceptable cert chains
    ca_cert_object_list = []
    for ca in ca_cert_pem_file_names:
      ca_cert_object_list.append(vcon.security.load_pem_cert(ca)[0])

    last_exception = Exception("Internal error in Vcon.verify this exception should never be thrown")
    chain_count = 0
    for signature in self._jws_dict['signatures']:
      if('header' in signature):
        if('x5c' in signature['header']):
          x5c = signature['header']['x5c']
          chain_count += 1

          cert_chain_objects = vcon.security.der_to_certs(x5c)

          # TODO: some of this should be move to the security submodule
          # e.g. the iterating over CAs

          # TODO: need to do something a little smarter on the exception raise to
          # give a clue of the best/closest chain and CA that failed.  Perhaps
          # even all of the failures.

          try:
            vcon.security.verify_cert_chain(cert_chain_objects)

            # We have a valid chain, check if its from one of the accepted CAs
            for ca_object in ca_cert_object_list:
              try:
                vcon.security.verify_cert(cert_chain_objects[len(cert_chain_objects) - 1], ca_object)

                # IF we get here, we have a valid chain: cert_chain_objects issued from one of our accepted
                # CAs: ca_object.
                # The assumtion is that it is safe to trust this cert chain.  So we
                # can use it to build a JWK and verify the signature.
                verification_jwk = {}
                verification_jwk["kty"] = "RSA"
                verification_jwk["use"] = "sig"
                verification_jwk["alg"] = signature['header']['alg']
                verification_jwk["e"] = jose.utils.base64url_encode(jose.utils.long_to_bytes(cert_chain_objects[0].public_key().public_numbers().e)).decode('utf-8')
                verification_jwk["n"] = jose.utils.base64url_encode(jose.utils.long_to_bytes(cert_chain_objects[0].public_key().public_numbers().n)).decode('utf-8')

                jws_token = signature['protected'] + "." + self._jws_dict['payload'] + "." + signature['signature']
                verified_payload = jose.jws.verify(jws_token, verification_jwk, verification_jwk["alg"])

                # If we get here, the payload was verified
                #print("verified payload: {}".format(verified_payload))
                #print("verified payload type: {}".format(type(verified_payload)))
                vcon_dict = json.loads(verified_payload.decode('utf-8'))
                self._vcon_dict = self.migrate_0_0_1_vcon(vcon_dict)

                self._state = VconStates.VERIFIED

                return(None)

              # This valid chain, is not issued from the CA for this ca_objjwk
              except Exception as e:
                last_exception = e
                # Keep trying other CAs until we run out or succeed

          # Invalid chain
          except Exception as e:
            last_exception = e
            # Keep trying other chains until we run out or succeed

    if(chain_count == 0):
      raise InvalidVconSignature("None of the signatures contain the x5c chain, which this implementation currenlty requires.")

    raise last_exception


  def encrypt(self, cert_pem_file_name : str) -> None:
    """
    encrypt a Signed vcon using the given public key from the give certificate.

    vcon must be signed first.

    Parameters:
    cert_pem_file_name (str): the public key/cert to use for encrypting the vcon.

    Returns: none
    """

    if(self._state not in [VconStates.SIGNED, VconStates.UNVERIFIED]):
      raise InvalidVconState("Vcon must be signed before it can be encrypted")

    if(len(self._jws_dict) < 2):
      raise InvalidVconState("Vcon signature does not seem valid: {}".format(self._jws_dict))

    # both of these work
    #encryption = "A256GCM"
    encryption = "A256CBC-HS512"

    encryption_key = vcon.security.build_encryption_jwk_from_pem_file(cert_pem_file_name)

    plaintext = json.dumps(self._jws_dict)

    jwe_compact_token = jose.jwe.encrypt(plaintext, encryption_key, encryption, encryption_key['alg']).decode('utf-8')
    jwe_complete_serialization = vcon.security.jwe_compact_token_to_complete_serialization(jwe_compact_token, enc = encryption, x5c = [])
    self._jwe_dict = jwe_complete_serialization
    self._state = VconStates.ENCRYPTED

  def decrypt(self, private_key_pem_file_name : str, cert_pem_file_name : str) -> None:
    """
    Decrypt a vCon using private and public key file.
  
    vCOn must be in encrypted state and will be in signed state after decryption.

    Parameters:
    cert_pem_file_name (str): the public key/cert to use for decrypting the vcon.

    private_key_pem_file_name (str): the private key to use for decrypting the vcon.

    Returns: none
    """

    if(self._state != VconStates.ENCRYPTED):
      raise InvalidVconState("Vcon is not encerypted")

    if(len(self._jwe_dict) < 2):
      raise InvalidVconState("Vcon JWE does not seem valid: {}".format(self._jws_dict))

    jwe_compact_token_reconstructed = vcon.security.jwe_complete_serialization_to_compact_token(self._jwe_dict)

    (header, signing_key) = vcon.security.build_signing_jwk_from_pem_files(private_key_pem_file_name, [cert_pem_file_name])
    #signing_key['alg'] = encryption_key['alg']

    plaintext_decrypted = jose.jwe.decrypt(jwe_compact_token_reconstructed, signing_key).decode('utf-8')
    # let loads figure out if this is an encrypted JWS vCon or just a vCon
    current_state = self._state
    # Fool loads into thinking this is a raw vCon and its safe to load.  Save state incase we barf.
    self._state = VconStates.UNSIGNED
    try:
      self.loads(plaintext_decrypted)

    except Exception as e:
      # restore state
      self._state = current_state
      raise e

  def add_uuid(self, domain_name: str) -> str:
    """
    Generate a UUID for this vCon and set the parameter

    Parameters:
      domain_name: a DNS domain name string, should generally be a fully qualified host
          name.

    Returns:
      UUID version 8 string
      (vCon uuid parameter is also set)

    """

    uuid = self.uuid8_domain_name(domain_name)

    self._vcon_dict[Vcon.UUID] = uuid

    return(uuid)

  @staticmethod
  def uuid8_domain_name(domain_name: str) -> str:
    """
    Generate a version 8 (custom) UUID using the upper 62 bits of the SHA-1 hash
    for the given DNS domain name string for custom_c and generating
    custom_a and custom_b the same way as unix_ts_ms and rand_a respectively
    for UUID version 7 (per IETF I-D draft-peabody-dispatch-new-uuid-format-04).

    Parameters:
      domain_name: a DNS domain name string, should generally be a fully qualified host
          name.

    Returns:
      UUID version 8 string
    """

    sha1_hasher = hashlib.sha1()
    sha1_hasher.update(bytes(domain_name, "utf-8"))
    dn_sha1 = sha1_hasher.digest()

    hash_upper_64 = dn_sha1[0:8]
    int64 = int.from_bytes(hash_upper_64, byteorder="big")

    uuid8_domain = Vcon.uuid8_time(int64)

    return(uuid8_domain)

  @staticmethod
  def uuid8_time(custom_c_62_bits: int) -> str:
    """
    Generate a version 8 (custom) UUID using the given custom_c and generating
    custom_a and custom_b the same way as unix_ts_ms and rand_a respectively
    for UUID version 7 (per IETF I-D draft-peabody-dispatch-new-uuid-format-04).

    Parameters:
      custom_c_62_bits: the 62 bit value as an integer to be used for custom_b
           portion of UUID version 8.

    Returns:
      UUID version 8 string
    """
    # This is partially from uuid6.uuid7 implementation:
    global _last_v8_timestamp

    nanoseconds = time.time_ns()
    if _last_v8_timestamp is not None and nanoseconds <= _last_v8_timestamp:
        nanoseconds = _last_v8_timestamp + 1
    _last_v7_timestamp = nanoseconds
    timestamp_ms, timestamp_ns = divmod(nanoseconds, 10**6)
    subsec = uuid6._subsec_encode(timestamp_ns)

    # This is not what is in the vCon I-D.  It says random bits
    # not bits from the time stamp.  May want to change this
    subsec_a = subsec >> 8
    uuid_int = (timestamp_ms & 0xFFFFFFFFFFFF) << 80
    uuid_int |= subsec_a << 64
    uuid_int |= custom_c_62_bits

    # We lie about the version and then correct it afterwards
    uuid_str = str(uuid6.UUID(int=uuid_int, version=7))
    assert(uuid_str[14] == '7')
    uuid_str =  uuid_str[:14] +'8' + uuid_str[15:]

    return(uuid_str)

  @staticmethod
  def migrate_0_0_1_vcon(old_vcon : dict) -> dict:
    """
    Migrate/translate an an older deprecated vCon to the current version.

    Parameters:
      old_vcon old format 0.0.1 vCon

    Returns:
      the modified old_vcon in the new format
    """

    # Fix dates in older dialogs
    for index, dialog in enumerate(old_vcon["dialog"]):
      if("start" in dialog):
        dialog['start'] = vcon.utils.cannonize_date(dialog['start'])

      if("alg" in dialog):
        if( dialog['alg'] == "lm-ots"):
          dialog['alg'] = "LMOTS_SHA256_N32_W8"
        elif( dialog['alg'] in ["SHA-512", "LMOTS_SHA256_N32_W8"]):
          pass
        else:
          raise AttributeError("dialog[{}] alg: {} not supported.  Must be SHA-512 or LMOTS_SHA256_N32_W8".format(index, dialog['alg']))

    # Translate transcriptions to body for consistency with dialog and attachments
    for index, analysis in enumerate(old_vcon["analysis"]):
      if(analysis['type'] == "transcript"):
        if("transcript" in analysis):
          analysis['body'] = analysis.pop('transcript')

          if(isinstance(analysis['body'], dict)):
            analysis['encoding'] = "json"
          elif(isinstance(analysis['body'], str)):
            analysis['encoding'] = "none"

          else:
            raise Exception("body type: {} in analysis[{}] not recognized".format(type(analysis['body']), index))

    return(old_vcon)

