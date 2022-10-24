"""
unit tests for UUID generation and setting of uuid parameter
"""

import pytest
import vcon

def test_uuid8_time() -> None:

  uuid = vcon.Vcon.uuid8_time(0)
  assert(uuid[8] == '-')
  assert(uuid[13] == '-')
  assert(uuid[18] == '-')
  assert(uuid[23] == '-')
  assert(uuid[14] == '8')
  assert(uuid[18:] == '-8000-000000000000')

  print("uuid null rand_b: {}".format(uuid))

def test_uuid8_domain_name() -> None:
  uuid = vcon.Vcon.uuid8_domain_name("example.com")
  print(uuid)

def test_vcon_uuid() -> None:
  new_vcon = vcon.Vcon()
  new_vcon.set_uuid("example.com")
  print("{} len: {}".format(new_vcon._vcon_dict["uuid"], len(new_vcon._vcon_dict[vcon.Vcon.UUID])))
  assert(len(new_vcon._vcon_dict[vcon.Vcon.UUID]) == 36)

  try:
    new_vcon.set_uuid("example.com")
    raise Exception("Expected an exception to be thrown for UUID alread set")

  except AttributeError as e:
    # Expected this as UUID is already set
    pass

  # This should allow UUID to be updated
  new_vcon.set_uuid("example.com", replace=True)

  # Test serialization
  copy_vcon = vcon.Vcon()
  copy_vcon.loads(new_vcon.dumps())
  assert(len(copy_vcon._vcon_dict[vcon.Vcon.UUID]) == 36)
  assert(copy_vcon._vcon_dict[vcon.Vcon.UUID] == new_vcon._vcon_dict[vcon.Vcon.UUID])
  assert(copy_vcon.uuid == new_vcon._vcon_dict[vcon.Vcon.UUID])

  try:
    copy_vcon.uuid = "foo"
    raise Exception("Failed to prevent setting of uuid attribute")

  except AttributeError as e:
    # expected exception as uuid is read only attribute
    pass



