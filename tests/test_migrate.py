"""
Unit test for migration of vCon versions
"""

import vcon
import vcon.security

def test_migrate_0_0_1():
  vcon_json = vcon.security.load_string_from_file("tests/pre_0.0.1_vcon_trans.vcon")

  migrated_vcon = vcon.Vcon()
  migrated_vcon.loads(vcon_json)

  assert("body" in migrated_vcon.analysis[0])
  assert("transcript" not in migrated_vcon.analysis[0])
  assert("encoding" in migrated_vcon.analysis[0])
  assert(migrated_vcon.analysis[0]["encoding"] == "json")
  assert(migrated_vcon.analysis[0]["body"]['a'] == "b")
  assert(migrated_vcon.analysis[0]["body"]['c'] == 3)

  # Should be converted to RFC3339 format date
  assert(migrated_vcon.dialog[0]['start'] == "2022-05-18T23:05:05.000+00:00")



