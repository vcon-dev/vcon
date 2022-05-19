#!/usr/bin/python3

import pytest
import vcon
import json

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
  if(test_list != None):
    assert(len(test_list) == size)
  else:
    assert(size == 0)

def assert_vcon_array_size(vCon : vcon.vcon, list_name : str, size : int) -> None:
  assert_dict_array_size(vCon._vcon_dict, list_name, size)

@pytest.fixture
def empty_vcon() -> vcon.vcon:
  return(vcon.vcon())

@pytest.fixture
def two_party_tel_vcon(empty_vcon : vcon.vcon) -> vcon.vcon:
  vCon = empty_vcon
  first_party = vCon.set_party_tel_url(call_data['source'])
  vCon.set_party_join_time(call_data['rfc2822'], first_party)
  second_party = vCon.set_party_tel_url(call_data['destination'])
  vCon.set_party_join_time(call_data['rfc2822'], second_party)
  return(vCon)

def test_tel(empty_vcon : vcon.vcon):
  """ Test adding first party with a tel url to create simple vCon """

  vCon = empty_vcon
  assert_vcon_array_size(vCon, "participants", 0)
  party_index = vCon.set_party_tel_url(call_data['source'])
  assert(party_index == 0)
  assert(vCon._vcon_dict["participants"][party_index]['tel'] == call_data['source'])
  assert_vcon_array_size(vCon, "participants", 1)
  assert_vcon_array_size(vCon, "dialog", 0)
  assert_vcon_array_size(vCon, "analysis", 0)
  assert_vcon_array_size(vCon, "attachments", 0)


def test_two_tel_party_vcon(empty_vcon : vcon.vcon) -> None:
  """ Test two party call with tel urls """
  vCon = empty_vcon

  # 1st party:
  assert_vcon_array_size(vCon, "participants", 0)
  assert_vcon_array_size(vCon, "dialog", 0)
  assert_vcon_array_size(vCon, "analysis", 0)
  assert_vcon_array_size(vCon, "attachments", 0)
  first_party = vCon.set_party_tel_url(call_data['source'])
  assert(first_party == 0)
  assert(vCon._vcon_dict["participants"][first_party]['tel'] == call_data['source'])
  assert_vcon_array_size(vCon, "participants", 1)

  # 2nd party:
  second_party = vCon.set_party_tel_url(call_data['destination'])
  assert(second_party== 1)
  assert(vCon._vcon_dict["participants"][second_party]['tel'] == call_data['destination'])
  # make sure 1st party did not get modified
  assert(vCon._vcon_dict["participants"][first_party]['tel'] == call_data['source'])
  assert_vcon_array_size(vCon, "participants", 2)
  assert_vcon_array_size(vCon, "dialog", 0)
  assert_vcon_array_size(vCon, "analysis", 0)
  assert_vcon_array_size(vCon, "attachments", 0)

def test_dumps(two_party_tel_vcon : vcon.vcon) -> None:
  vCon = two_party_tel_vcon
  
  vcon_json = vCon.dumps()
  vcon_dict = json.loads(vcon_json)

  assert(vcon_dict["vcon"] == "0.0.1")
  assert_dict_array_size(vcon_dict, "participants", 2)
  assert(vcon_dict['participants'][0]['tel'] == call_data['source'])
  assert(vcon_dict['participants'][1]['tel'] == call_data['destination'])
  assert(vcon_dict['participants'][0]['joined'] == call_data['rfc2822'])
  assert(vcon_dict['participants'][1]['joined'] == call_data['rfc2822'])
  assert_dict_array_size(vcon_dict, "dialog", 0)
  assert_dict_array_size(vcon_dict, "analysis", 0)
  assert_dict_array_size(vcon_dict, "attachments", 0)
  
def test_loads(two_party_tel_vcon : vcon.vcon, empty_vcon : vcon.vcon) -> None:
  vcon_json = two_party_tel_vcon.dumps()
  empty_vcon.loads(vcon_json)

  assert(empty_vcon._vcon_dict["participants"][0]['tel'] == call_data['source'])
  assert(empty_vcon._vcon_dict["participants"][1]['tel'] == call_data['destination'])
  assert(empty_vcon._vcon_dict["participants"][0]['joined'] == call_data['rfc2822'])
  assert(empty_vcon._vcon_dict["participants"][1]['joined'] == call_data['rfc2822'])

