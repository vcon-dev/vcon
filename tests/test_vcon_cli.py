"""
unit tests for the vcon command line script
"""

import pytest
import vcon.cli
import sys

def test_vcon_new(capsys):
  # Note: can provide stdin using:
  # sys.stdin = io.StringIO('{"vcon": "0.0.1", "parties": [], "dialog": [], "analysis": [], "attachments": [], "uuid": "0183866c-df92-89ab-973a-91e26eb8001b"}')
  vcon.cli.main(["-n"])

  new_vcon_json, error = capsys.readouterr()

  # As we captured the stderr, we need to re-emmit it for unit test feedback
  print("stderr: {}".format(error), file=sys.stderr)

  new_vcon = vcon.Vcon()
  new_vcon.loads(new_vcon_json)
  assert(len(new_vcon.uuid) == 36)
  assert(new_vcon.vcon == "0.0.1")
