""" Unit test for party search methods """

import pytest
import vcon

def test_party_search():
  vCon = vcon.Vcon()
  assert(len(vCon.parties) == 0)

  vCon.set_party_parameter("tel", "+16171234567")
  vCon.set_party_parameter("tel", "+16171111111")
  vCon.set_party_parameter("tel", "+16170000000")
  vCon.set_party_parameter("tel", "+18571234567")
  assert(len(vCon.parties) == 4)

  vCon.set_party_parameter("mailto", "a@example.com", 3)
  assert(len(vCon.parties) == 4)

  vCon.set_party_parameter("mailto", "b@example.com")
  vCon.set_party_parameter("mailto", "c@example.com")
  vCon.set_party_parameter("mailto", "a@foo.com")
  assert(len(vCon.parties) == 7)

  found = vCon.find_parties_by_parameter("tel", "+1617")
  assert(len(found) == 3)

  found = vCon.find_parties_by_parameter("tel", "1234567")
  assert(len(found) == 2)

  found = vCon.find_parties_by_parameter("mailto", "@example.com")
  assert(len(found) == 3)

  found = vCon.find_parties_by_parameter("mailto", "a@")
  assert(len(found) == 2)

  found = vCon.find_parties_by_parameter("mailto", "xxx")
  assert(len(found) == 0)

  found = vCon.find_parties_by_parameter("mailto", "a@example.com")
  assert(len(found) == 1)

  found = vCon.find_parties_by_parameter("name", "xxx")
  assert(len(found) == 0)
