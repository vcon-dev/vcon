"""
unit tests for the vcon command line script
"""

import sys
import io
import os.path
#import json
import pytest

IN_VCON_JSON = '{"uuid": "0183878b-dacf-8e27-973a-91e26eb8001b", "vcon": "0.0.1", "attachments": [], "parties": [{"name": "Alice", "tel": "+12345678901"}, {"name": "Bob", "tel": "+19876543210"}]}'
WAVE_FILE_NAME = "examples/agent_sample.wav"
WAVE_FILE_URL = "https://github.com/vcon-dev/vcon/blob/main/examples/agent_sample.wav?raw=true"
WAVE_FILE_SIZE = os.path.getsize(WAVE_FILE_NAME)
VCON_WITH_DIALOG_FILE_NAME = "examples/test.vcon"

def test_vcon_new(capsys):
  """test vcon -n"""
  # Importing vcon here so that we catch any junk stdout which will break ths CLI
  import vcon.cli
  # Note: can provide stdin using:
  # sys.stdin = io.StringIO('{"vcon": "0.0.1", "parties": [], "dialog": [], "analysis": [], "attachments": [], "uuid": "0183866c-df92-89ab-973a-91e26eb8001b"}')
  vcon.cli.main(["-n"])

  new_vcon_json, error = capsys.readouterr()
  # As we captured the stderr, we need to re-emmit it for unit test feedback
  print("stderr: {}".format(error), file=sys.stderr)

  new_vcon = vcon.Vcon()
  try:
    new_vcon.loads(new_vcon_json)
  except Exception as e:
    print("Most likely an error has occurred as something has written to stdout, causing junk to be include in the JSON also on stdout")
    print("*****\n{}\n*****".format(new_vcon_json))
    raise e

  assert(len(new_vcon.uuid) == 36)
  assert(new_vcon.vcon == "0.0.1")

def test_filter_plugin_register(capsys):
  """ Test cases for the register filter plugin CLI option -r """
  # Importing vcon here so that we catch any junk stdout which will break ths CLI
  import vcon.cli
  command_args = "-n -r foo2 doesnotexist.foo Foo filter foo2".format(VCON_WITH_DIALOG_FILE_NAME).split()
  # Filter registered, but module not found
  # expect vcon.filter_plugins.PluginModuleNotFound
  assert(len(command_args) == 7)

  try:
    vcon.cli.main(command_args)
    raise Exception("Expected this to throw vcon.filter_plugins.PluginModuleNotFound as the module name is wrong")

  except vcon.filter_plugins.PluginModuleNotFound as no_mod_error:
    print("Got {}".format(no_mod_error))

  command_args = "-n -r foo2 tests.foo Foo filter foo2".format(VCON_WITH_DIALOG_FILE_NAME).split()
  # Filter register and loaded, but not completely implemented
  # expect vcon.filter_plugins.PluginFilterNotImplemented
  assert(len(command_args) == 7)

  try:
    vcon.cli.main(command_args)
    raise Exception("Expected this to throw vcon.filter_plugins.PluginFilterNotImplemented as the module name is wrong")

  except vcon.filter_plugins.PluginFilterNotImplemented as mod_not_impl_error:
    print("Got {}".format(mod_not_impl_error))

def test_filter(capsys):
  """ Test cases for the filter command to run filer plugins """
  # Importing vcon here so that we catch any junk stdout which will break ths CLI
  import vcon.cli
  command_args = "-i {} filter transcribe -fo '{{\"model_size\":\"base\"}}'".format(VCON_WITH_DIALOG_FILE_NAME).split()
  assert(len(command_args) == 6)

  vcon.cli.main(command_args)

  # Get stdout and stderr
  out_vcon_json, error = capsys.readouterr()

  # As we captured the stderr, we need to re-emmit it for unit test feedback
  print("stderr: {}".format(error), file=sys.stderr)

  # stdout should be a Vcon with analysis added
  out_vcon = vcon.Vcon()
  try:
    out_vcon.loads(out_vcon_json)
  except Exception as e:
    print("output Vcon JSON: {}".format(out_vcon_json[0:30]))
    raise e


  assert(len(out_vcon.dialog) == 1)
  assert(len(out_vcon.analysis) == 3)

def test_ext_recording(capsys):
  """test vcon add ex-recording"""
  # Importing vcon here so that we catch any junk stdout which will break ths CLI
  import vcon.cli
  date = "2022-06-21T17:53:26.000+00:00"
  parties = "[0,1]"

  # Setup stdin for vcon CLI to read
  sys.stdin = io.StringIO(IN_VCON_JSON)

  # Run the vcon command to ad externally reference recording
  vcon.cli.main(["add", "ex-recording", WAVE_FILE_NAME, date, parties, WAVE_FILE_URL])

  out_vcon_json, error = capsys.readouterr()
  # As we captured the stderr, we need to re-emmit it for unit test feedback
  print("stderr: {}".format(error), file=sys.stderr)

  out_vcon = vcon.Vcon()
  out_vcon.loads(out_vcon_json)

  assert(len(out_vcon.dialog) == 1)
  #print(json.dumps(json.loads(out_vcon_json), indent=2))
  assert(out_vcon.dialog[0]["type"] ==  "recording")
  assert(out_vcon.dialog[0]["start"] == date)
  assert(out_vcon.dialog[0]["duration"] == 566.496)
  assert(len(out_vcon.parties) == 2)
  assert(out_vcon.dialog[0]["parties"][0] == 0)
  assert(out_vcon.dialog[0]["parties"][1] == 1)
  assert(out_vcon.dialog[0]["url"] == WAVE_FILE_URL)
  assert(out_vcon.dialog[0]["mimetype"] == "audio/x-wav")
  assert(out_vcon.dialog[0]["filename"] == WAVE_FILE_NAME)
  assert(out_vcon.dialog[0]["signature"] == "MfZG-8n8eU5pbMWN9c_SyTyN6l1zwGWNg43h2n-K1q__XVgdxz1X2H3Wbg4I9VZImQKCRqgYHxJjrdIXDAXO8w")
  assert(out_vcon.dialog[0]["alg"] == "SHA-512")
  assert(out_vcon.vcon == "0.0.1")
  assert(out_vcon.uuid == "0183878b-dacf-8e27-973a-91e26eb8001b")

  assert(out_vcon.dialog[0].get("body") is None )
  assert(out_vcon.dialog[0].get("encoding") is None )

def test_int_recording(capsys):
  """test vcon add in-recording"""
  # Importing vcon here so that we catch any junk stdout which will break ths CLI
  import vcon.cli
  date = "2022-06-21T17:53:26.000+00:00"
  parties = "[0,1]"

  # Setup stdin for vcon CLI to read
  sys.stdin = io.StringIO(IN_VCON_JSON)

  # Run the vcon command to ad externally reference recording
  vcon.cli.main(["add", "in-recording", WAVE_FILE_NAME, date, parties])

  out_vcon_json, error = capsys.readouterr()
  # As we captured the stderr, we need to re-emmit it for unit test feedback
  print("stderr: {}".format(error), file=sys.stderr)

  out_vcon = vcon.Vcon()
  out_vcon.loads(out_vcon_json)

  assert(len(out_vcon.dialog) == 1)
  #print(json.dumps(json.loads(out_vcon_json), indent=2))
  assert(out_vcon.dialog[0]["type"] ==  "recording")
  assert(out_vcon.dialog[0]["start"] == date)
  assert(out_vcon.dialog[0]["duration"] == 566.496)
  assert(len(out_vcon.parties) == 2)
  assert(out_vcon.dialog[0]["parties"][0] == 0)
  assert(out_vcon.dialog[0]["parties"][1] == 1)
  assert(out_vcon.dialog[0]["mimetype"] == "audio/x-wav")
  assert(out_vcon.dialog[0]["filename"] == WAVE_FILE_NAME)
  assert(out_vcon.vcon == "0.0.1")
  assert(out_vcon.uuid == "0183878b-dacf-8e27-973a-91e26eb8001b")
# File is base64url encodes so size will be 4/3 larger
  assert(len(out_vcon.dialog[0]["body"]) == WAVE_FILE_SIZE / 3 * 4)
  assert(out_vcon.dialog[0]["encoding"] == "base64url")

  assert(out_vcon.dialog[0].get("url") is None)
  assert(out_vcon.dialog[0].get("signature") is None)
  assert(out_vcon.dialog[0].get("alg") is None)

# TODO:
# vcon add in-email
# vcon sign
# vcon verify
# vcon encrypt
# vcon decrypt
# vcon extract dialog
# vcon -i
# vcon -o

