""" Whisper transcription plugin unit test """

import os
import datetime
import pytest
import json
import vcon
import vcon.filter_plugins

def test_whisper_registration():
  options = {"model_size" : "base"}

  plugin = vcon.filter_plugins.FilterPluginRegistry.get("whisper")
  assert(plugin is not None)
  assert(plugin.import_plugin(**options) == True)

def test_plugin_method_add():
  in_vcon = vcon.Vcon()

def test_whisper_transcribe_inline_dialog():
  in_vcon = vcon.Vcon()

  options = {"llanguage" : "en", "model_size" : "base", "output_options" : ["vendor", "word_srt", "word_ass"], "whisper" : { "language" : "en"} }
  with open("examples/test.vcon", "r") as vcon_file:
    in_vcon.load(vcon_file)

  assert(len(in_vcon.dialog) > 0)

  anal_count = len(in_vcon.analysis)
  out_vcon = in_vcon.whisper(**options)
  assert(len(in_vcon.analysis) == anal_count + 3) # Whisper transcript, srt file and ass file
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
  print("transcript keys: {}".format(out_vcon.analysis[anal_count]["body"].keys()))
  # Stable whisper changed and the word time stamps are now part of "segments" in transcription object
  #assert(body_len == 4) # keys in dict
  assert(body_len == 3) # keys in dict
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

def test_whisper_transcribe_external_dialog():
  in_vcon = vcon.Vcon()

  # Add external ref
  file_path = "examples/agent_sample.wav"
  url = "https://github.com/vcon-dev/vcon/blob/main/examples/agent_sample.wav?raw=true"
  file_content = b""
  with open(file_path, "rb") as file_handle:
    file_content = file_handle.read()
    print("body length: {}".format(len(file_content)))
    assert(len(file_content) > 10000)

  dialog_index = in_vcon.add_dialog_external_recording(file_content,
    datetime.datetime.utcnow(),
    0, # duration TODO
    [0,1],
    url,
    vcon.Vcon.MIMETYPE_AUDIO_WAV,
    os.path.basename(file_path))

  assert(dialog_index == 0)

  options = {"llanguage" : "en", "model_size" : "base", "output_options" : ["vendor", "word_srt", "word_ass"], "whisper" : { "language" : "en"} }

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
  print("transcript keys: {}".format(out_vcon.analysis[anal_count]["body"].keys()))
  # Stable whisper changed and the word time stamps are now part of "segments" in transcription object
  #assert(body_len == 4) # keys in dict
  assert(body_len == 3) # keys in dict
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
