"""
Unit tests for external content such as recording, attachments which are stored
as URLs with a signature for the content stored else where.  Using
Leighton-Micali One Time Signature (RFC8554).
"""

import os
import datetime
import pytest
import vcon
import vcon.security
import hsslms
import hashlib
import jose.utils

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
  first_party = vCon.set_party_parameter("tel", call_data['source'])
  second_party = vCon.set_party_parameter("tel", call_data['destination'])
  vCon.set_uuid("vcon.dev")
  return(vCon)

def test_lm_ots_sign() -> None:
  file_size = 2048
  fake_file = os.urandom(file_size)

  key, sig = vcon.security.lm_one_time_signature(fake_file)

  vcon.security.verify_lm_one_time_signature(fake_file, sig, key)

  try:
    # cause signature to fail
    vcon.security.verify_lm_one_time_signature(fake_file, sig.replace("D", "E", 1), key)
    raise Exception("Should have raisee and INVALID signature error")

  except hsslms.utils.INVALID as invalid_error:
    # Expect this to be raised as we have modified signature
    pass

  try:
    # cause key to fail
    vcon.security.verify_lm_one_time_signature(fake_file, sig, key.replace("A", "Z", 1))
    raise Exception("Should have raised and INVALID key error")

  except hsslms.utils.INVALID as invalid_error:
    # Expect this to be raised as we have modified signature
    pass

def test_get_external_recording(two_party_tel_vcon : vcon.Vcon) -> None:
  # Add external ref
  file_path = "examples/agent_sample.wav"
  url = "https://github.com/vcon-dev/vcon/blob/main/examples/agent_sample.wav?raw=true"
  file_content = b""
  with open(file_path, "rb") as file_handle:
    file_content = file_handle.read()
    print("body length: {}".format(len(file_content)))
    assert(len(file_content) > 10000)

  dialog_index = two_party_tel_vcon.add_dialog_external_recording(file_content,
    datetime.datetime.utcnow(),
    0, # duration TODO
    [0,1],
    url,
    vcon.Vcon.MIMETYPE_AUDIO_WAV,
    os.path.basename(file_path))

  assert(dialog_index == 0)

  dialog_object = two_party_tel_vcon.dialog[0]
  assert(dialog_object.get("originator", None) is None)
  assert(dialog_object.get("duration", None) == 0)
  assert(dialog_object.get("url", None) == url)

  body_bytes = two_party_tel_vcon.get_dialog_external_recording(dialog_index)
  assert(len(file_content) == len(body_bytes))
  assert(file_content == body_bytes)

  # This should be valid
  two_party_tel_vcon.verify_dialog_external_recording(0, body_bytes)
  
  body_byte_array = bytearray(body_bytes)
  body_byte_array[0] = body_bytes[0] + 1
  body_bytes = bytes(body_byte_array)
  assert(file_content != body_bytes)

  try:
    #We modified the body_bytes so this should fail
    two_party_tel_vcon.verify_dialog_external_recording(0, body_bytes)
    raise Exception("Should have thrown invalid as body_bytes is not identical")

  except vcon.InvalidVconHash as invalid_body_error:
    # We expect this to occur
    pass

def test_external_recording_lm_ots(two_party_tel_vcon : vcon.Vcon) -> None:
  data_size = 4096
  data = os.urandom(data_size)

  url = "https://example.com?q=\"ddd\"&y=\'!\'"
  #print("url: {}".format(url))

  file_name = "my_rec.wav"

  assert(vcon.Vcon.MIMETYPE_AUDIO_WAV == "audio/x-wav")

  two_party_tel_vcon.add_dialog_external_recording(data,
    call_data["rfc2822"],
    call_data["duration"],
    0,
    url,
    vcon.Vcon.MIMETYPE_AUDIO_WAV,
    file_name,
    sign_type="LM-OTS")

  vcon_json = two_party_tel_vcon.dumps()

  new_vcon = vcon.Vcon()
  new_vcon.loads(vcon_json)

  assert(len(new_vcon.dialog) == 1)
  assert(new_vcon.dialog[0]['type'] == "recording")
  assert(new_vcon.dialog[0]['url'] == url)
  assert(new_vcon.dialog[0]['parties'] == 0)
  assert(new_vcon.dialog[0]['start'] == call_data["rfc3339"])
  assert(new_vcon.dialog[0]['duration'] == call_data["duration"])
  assert(new_vcon.dialog[0]['mimetype'] == "audio/x-wav")
  assert(new_vcon.dialog[0]['filename'] == file_name)
  assert(new_vcon.dialog[0]['alg'] == 'LMOTS_SHA256_N32_W8')
  assert(len(new_vcon.dialog[0]['key']) > 1)
  assert("body" not in new_vcon.dialog[0])

  new_vcon.verify_dialog_external_recording(0, data)

  try:
    # Change the data so that validation should fail
    new_vcon.verify_dialog_external_recording(0, data[1:])
    raise Exception("Should have raised exception here as data is missin the first byte")

  except hsslms.utils.INVALID as invalid_error:
    # Expect to get this exception
    pass

def test_sha512():
  data1 = b"test some text stuff as binary"
  data_size = 4096
  data2 = os.urandom(data_size)

  hasher = hashlib.sha512()

  hasher.update(data1)
  hasher.update(data2)

  sig_hash = jose.utils.base64url_encode(hasher.digest())

  validater = hashlib.sha512()

  validater.update(data1 + data2)

  validate_hash = jose.utils.base64url_encode(validater.digest())

  assert(sig_hash == validate_hash)

def test_external_recording_sha_512(two_party_tel_vcon : vcon.Vcon) -> None:
  data_size = 4096
  data = os.urandom(data_size)

  url = "https://example.com?q=\"ddd\"&y=\'!\'"
  #print("url: {}".format(url))

  file_name = "my_rec.wav"

  assert(vcon.Vcon.MIMETYPE_AUDIO_WAV == "audio/x-wav")

  two_party_tel_vcon.add_dialog_external_recording(data,
    call_data["rfc2822"],
    call_data["duration"],
    0,
    url,
    vcon.Vcon.MIMETYPE_AUDIO_WAV,
    file_name,
    originator=1)

  vcon_json = two_party_tel_vcon.dumps()

  print("original: {}".format(vcon_json))
  new_vcon = vcon.Vcon()
  new_vcon.loads(vcon_json)
  print("deserialized: {}".format(new_vcon.dumps()))

  assert(len(new_vcon.dialog) == 1)
  assert(new_vcon.dialog[0]['type'] == "recording")
  assert(new_vcon.dialog[0]['url'] == url)
  assert(new_vcon.dialog[0]['parties'] == 0)
  assert(new_vcon.dialog[0]['start'] == call_data["rfc3339"])
  assert(new_vcon.dialog[0]['duration'] == call_data["duration"])
  assert(new_vcon.dialog[0]['mimetype'] == "audio/x-wav")
  assert(new_vcon.dialog[0]['filename'] == file_name)
  assert(new_vcon.dialog[0]['alg'] == 'SHA-512')
  assert(new_vcon.dialog[0]['originator'] == 1)
  assert("body" not in new_vcon.dialog[0])
  assert("key" not in new_vcon.dialog[0])

  new_vcon.verify_dialog_external_recording(0, data)

  try:
    # Change the data so that validation should fail
    new_vcon.verify_dialog_external_recording(0, data[1:])
    raise Exception("Should have raised exception here as data is missin the first byte")

  except vcon.InvalidVconHash as invalid_error:
    # Expect to get this exception
    pass
