""" Whisper transcription plugin unit test """

import pytest
import json
import vcon
import vcon.filter_plugins

def test_whisper_registration():
  options = {"model_size" : "base"}

  plugin = vcon.filter_plugins.FilterPluginRegistry.get("whisper")
  assert(plugin is not None)
  assert(plugin.import_plugin(**options) == True)

def test_whisper_transcribe():
  in_vcon = vcon.Vcon()

  options = {"llanguage" : "en", "model_size" : "base", "output_options" : ["vendor", "word_srt", "word_ass"], "whisper" : { "language" : "en"} }
  with open("examples/test.vcon", "r") as vcon_file:
    in_vcon.load(vcon_file)

  assert(len(in_vcon.dialog) > 0)

  anal_count = len(in_vcon.analysis)
  out_vcon = in_vcon.transcribe(**options)
  assert(len(out_vcon.analysis) == anal_count + 3) # Whisper transcript, srt file and ass file
  #print(json.dumps(out_vcon.analysis[0], indent=2))

  assert(out_vcon.analysis[anal_count]["type"] == "transcript")
  assert(out_vcon.analysis[anal_count]["vendor"] == "Whisper")
  assert(out_vcon.analysis[anal_count]["vendor_schema"] == "whisper_word_timestamps")
  #print("whisper body: {}".format(out_vcon.analysis[anal_count]["body"]))
  body_len = len(out_vcon.analysis[anal_count]["body"])
  #body_type = type(out_vcon.analysis[anal_count]["body"])
  assert(isinstance(out_vcon.analysis[anal_count]["body"], dict))
  #print("transcript type: {}".format(body_type))
  print("transcript len: {}".format(body_len))
  assert(body_len == 4) # keys in dict
  assert(out_vcon.analysis[anal_count + 1]["type"] == "transcript")
  assert(out_vcon.analysis[anal_count + 1]["vendor"] == "Whisper")
  assert(out_vcon.analysis[anal_count + 1]["vendor_schema"] == "whisper_word_srt")
  body_len = len(out_vcon.analysis[anal_count + 1]["body"])
  print("srt len: {}".format(body_len))
  expected_srt_size = 33000
  if(body_len < expected_srt_size):
    print("srt body: {}".format(out_vcon.analysis[anal_count + 1]["body"]))
    print("srt type: {}".format(type(out_vcon.analysis[anal_count + 1]["body"])))
  assert(body_len > expected_srt_size)
  assert(out_vcon.analysis[anal_count + 2]["type"] == "transcript")
  assert(out_vcon.analysis[anal_count + 2]["vendor"] == "Whisper")
  assert(out_vcon.analysis[anal_count + 2]["vendor_schema"] == "whisper_word_ass")
  body_len = len(out_vcon.analysis[anal_count + 2]["body"])
  print("ass len: {}".format(body_len))
  assert(body_len > 90000)

  if(out_vcon.uuid is None):
    out_vcon.set_uuid("vcon.net")

  out_vcon_json = out_vcon.dumps()

  # TODO: should test more than one inokation of whisper plugin to be sure its ok to reuse
  # models for more than one transcription.
