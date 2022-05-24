""" unit tests for mimimum elements of vCon """

import pytest
import vcon
import json
import os
import jose.utils
import pprint

VCON_PARTIES = "parties"
VCON_DIALOG = "dialog"

call_data = {
      "epoch" : "1652552179",
      "destination" : "2117",
      "source" : "+19144345359",
      "rfc2822" : "Sat, 14 May 2022 18:16:19 -0000",
      "file_extension" : "WAV",
      "duration" : 94.84,
      "channels" : 1
}

def assert_dict_array_size(test_dict : dict, list_name : str, size : int) -> None:
  test_list = test_dict.get(list_name, None)
  if(test_list is not None):
    assert(len(test_list) == size)
  else:
    assert(size == 0)

def assert_vcon_array_size(vCon : vcon.Vcon, list_name : str, size : int) -> None:
  assert_dict_array_size(vCon._vcon_dict, list_name, size)

#empty_count = 0
@pytest.fixture(scope="function")
def empty_vcon() -> vcon.Vcon:
  """ construct vCon with no data """
  #empty_count += 1
  #print("empty invoked: {}".format(empty_count))
  vCon = vcon.Vcon()
  #print("empty_vcon invoked:")
  #pprint.pprint(vCon._vcon_dict)
  return(vCon)

@pytest.fixture(scope="function")
def two_party_tel_vcon(empty_vcon : vcon.Vcon) -> vcon.Vcon:
  """ construct vCon with two tel URL """
  vCon = empty_vcon
  first_party = vCon.set_party_tel_url(call_data['source'])
  second_party = vCon.set_party_tel_url(call_data['destination'])
  return(vCon)

def test_tel(empty_vcon : vcon.Vcon):
  """ Test adding first party with a tel url to create simple vCon """

  vCon = empty_vcon
  assert_vcon_array_size(vCon, VCON_PARTIES, 0)
  party_index = vCon.set_party_tel_url(call_data['source'])
  assert(party_index == 0)
  assert(vCon._vcon_dict[VCON_PARTIES][party_index]['tel'] == call_data['source'])
  assert_vcon_array_size(vCon, VCON_PARTIES, 1)
  assert_vcon_array_size(vCon, VCON_DIALOG, 0)
  assert_vcon_array_size(vCon, "analysis", 0)
  assert_vcon_array_size(vCon, "attachments", 0)


def test_two_tel_party_vcon(empty_vcon : vcon.Vcon) -> None:
  """ Test two party call with tel urls """
  vCon = empty_vcon

  # 1st party:
  assert_vcon_array_size(vCon, VCON_PARTIES, 0)
  assert_vcon_array_size(vCon, VCON_DIALOG, 0)
  assert_vcon_array_size(vCon, "analysis", 0)
  assert_vcon_array_size(vCon, "attachments", 0)
  first_party = vCon.set_party_tel_url(call_data['source'])
  assert(first_party == 0)
  assert(vCon._vcon_dict[VCON_PARTIES][first_party]['tel'] == call_data['source'])
  assert_vcon_array_size(vCon, VCON_PARTIES, 1)

  # 2nd party:
  second_party = vCon.set_party_tel_url(call_data['destination'])
  assert(second_party== 1)
  assert(vCon._vcon_dict[VCON_PARTIES][second_party]['tel'] == call_data['destination'])
  # make sure 1st party did not get modified
  assert(vCon._vcon_dict[VCON_PARTIES][first_party]['tel'] == call_data['source'])
  assert_vcon_array_size(vCon, VCON_PARTIES, 2)
  assert_vcon_array_size(vCon, VCON_DIALOG, 0)
  assert_vcon_array_size(vCon, "analysis", 0)
  assert_vcon_array_size(vCon, "attachments", 0)

def test_dumps(two_party_tel_vcon : vcon.Vcon) -> None:
  vCon = two_party_tel_vcon
  
  vcon_json = vCon.dumps()
  vcon_dict = json.loads(vcon_json)

  assert(vcon_dict["vcon"] == "0.0.1")
  assert_dict_array_size(vcon_dict, VCON_PARTIES, 2)
  assert(vcon_dict['parties'][0]['tel'] == call_data['source'])
  assert(vcon_dict['parties'][1]['tel'] == call_data['destination'])
  assert_dict_array_size(vcon_dict, VCON_DIALOG, 0)
  assert_dict_array_size(vcon_dict, "analysis", 0)
  assert_dict_array_size(vcon_dict, "attachments", 0)
  
def test_loads(two_party_tel_vcon : vcon.Vcon, empty_vcon : vcon.Vcon) -> None:
  vcon_json = two_party_tel_vcon.dumps()
  empty_vcon.loads(vcon_json)

  assert(empty_vcon._vcon_dict[VCON_PARTIES][0]['tel'] == call_data['source'])
  assert(empty_vcon._vcon_dict[VCON_PARTIES][1]['tel'] == call_data['destination'])

def test_add_inline_recording(two_party_tel_vcon : vcon.Vcon, empty_vcon : vcon.Vcon) -> None:
  """ Test add of a recording file inline to ensure base64 encode and decode are properly done. """
  vCon = two_party_tel_vcon
  deserialized_vcon = empty_vcon
  random_size = 4096
  fake_recording_file = os.urandom(random_size)
  assert(len(fake_recording_file) == random_size)
  assert_vcon_array_size(vCon, VCON_DIALOG, 0)
  # TODO: create some common mime type constants for convenience
  mime_type = "audio/x-wav"
  file_name = "fake.wav"
  duration = 77.4
  file_length = vCon.add_dialog_inline_recording(fake_recording_file, call_data['rfc2822'],
    duration, [0, 1], mime_type, file_name)

  assert(file_length == len(fake_recording_file))
  assert_vcon_array_size(vCon, VCON_DIALOG, 1)
  assert(vCon._vcon_dict[VCON_DIALOG][0]["type"] == "recording")
  assert(vCon._vcon_dict[VCON_DIALOG][0]["start"] == call_data['rfc2822'])
  assert(vCon._vcon_dict[VCON_DIALOG][0]["duration"] == duration)
  assert(vCon._vcon_dict[VCON_DIALOG][0]["mimetype"] == mime_type)
  assert(vCon._vcon_dict[VCON_DIALOG][0]["filename"] == file_name)
  assert(vCon._vcon_dict[VCON_DIALOG][0][VCON_PARTIES][0] == 0)
  assert(vCon._vcon_dict[VCON_DIALOG][0][VCON_PARTIES][1] == 1)
  assert(len(vCon._vcon_dict[VCON_DIALOG][0][VCON_PARTIES]) == 2)

  # This is wrong.  decode should take a string not bytes, but it fails without the bytes conversion
  # this is a bug in jose.baseurl_decode
  decoded_file = jose.utils.base64url_decode(bytes(vCon._vcon_dict[VCON_DIALOG][0]["body"], 'utf-8'))
  assert(decoded_file == fake_recording_file)

  # serialize and deserialize and check the copy too
  vcon_json = vCon.dumps()
  #pprint.pprint(vcon_json)
  deserialized_vcon.loads(vcon_json)
  # This is wrong.  decode should take a string not bytes, but it fails without the bytes conversion
  # this is a bug in jose.baseurl_decode
  decoded_file = jose.utils.base64url_decode(bytes(deserialized_vcon._vcon_dict[VCON_DIALOG][0]["body"], 'utf-8'))
  assert(decoded_file == fake_recording_file)

  # TODO check other recording fields

def test_enumerate_parties(two_party_tel_vcon : vcon.Vcon, empty_vcon : vcon.Vcon) -> None:
  """ Test party iterator """
  #print("two_party_vcon in enum:")
  #pprint.pprint(two_party_tel_vcon._vcon_dict)
  count = 0
  for index, party in two_party_tel_vcon.enumerate_parties():
    #print("two party: {}".format(party))
    if(index == 0):
      assert(party["tel"] == call_data["source"])
    elif(index == 1):
      assert(party["tel"] == call_data["destination"])
    else:
      assert(0)

    assert(index == count)
    count += 1

  empty_vcon = vcon.Vcon()
  #print("empty_vcon in enum:")
  #pprint.pprint(empty_vcon._vcon_dict)
  for index, party in empty_vcon.enumerate_parties():
    print("empty: {}".format(party))
    assert(party is None)
    assert(0)

def test_get_party(two_party_tel_vcon : vcon.Vcon, empty_vcon : vcon.Vcon) -> None:
   assert(empty_vcon.get_party(-1) is None)
   # TODO: fix this:
   # Something is messed up with this test or pytest as the empty_vcon 
   # has elements in the parties list
   #assert(empty_vcon.get_party(0) is None)
   #assert(empty_vcon.get_party(1) is None)

   party = two_party_tel_vcon.get_party(0)
   assert(party["tel"] == call_data["source"])

   party = two_party_tel_vcon.get_party(1)
   assert(party["tel"] == call_data["destination"])

   #assert(two_party_tel_vcon.get_party(2) is None)

