""" Unit test for filter plugin framework """

import pytest
import sys
import vcon
import vcon.filter_plugins

# test foo registration file
import tests.foo_reg

def test_registry():
  plugin_names = vcon.filter_plugins.FilterPluginRegistry.get_names()

  print("found {} plugins: {}".format(len(plugin_names), plugin_names))

  # Test foo a test plugin, not fully implemented
  plugin_foop = vcon.filter_plugins.FilterPluginRegistry.get("foop")
  assert(plugin_foop is not None)
  assert(plugin_foop.import_plugin() == True)
  try:
    plugin_foop.filter(None)
    # SHould not get here
    raise Exception("Should have thrown a PluginFilterNotImplemented exception")

  except vcon.filter_plugins.PluginFilterNotImplemented as not_found_error:
    # We are expecting this exception
    print("got {}".format(not_found_error), file=sys.stderr)
    #raise not_found_error

  # this time test foop using its registered name as a method
  try:
    in_vcon = vcon.Vcon()
    out_vcon = in_vcon.foop()
    # SHould not get here
    raise Exception("Should have thrown a PluginFilterNotImplemented exception")

  except vcon.filter_plugins.PluginFilterNotImplemented as not_found_error:
    # We are expecting this exception
    print("got {}".format(not_found_error), file=sys.stderr)
    #raise not_found_error

  try:
    plugin_barp = vcon.filter_plugins.FilterPluginRegistry.get("barp")
    raise Exception("Expected not to fine barp and throw exception")

  except vcon.filter_plugins.PluginFilterNotRegistered as not_reg_error:
    print(not_reg_error, file=sys.stderr)

  vcon.filter_plugins.FilterPluginRegistry.set_type_default_name("exclaim", "foop")
  assert(vcon.filter_plugins.FilterPluginRegistry.get_type_default_name("exclaim") == "foop")
  assert(vcon.filter_plugins.FilterPluginRegistry.get_type_default_name("bar") == None)
  assert(vcon.filter_plugins.FilterPluginRegistry.get_type_default_plugin("exclaim") == plugin_foop)

  # this time test foop using it set as default type exclaim name as a method
  try:
    in_vcon = vcon.Vcon()
    out_vcon = in_vcon.exclaim()
    # SHould not get here
    raise Exception("Should have thrown a PluginFilterNotImplemented exception")

  except vcon.filter_plugins.PluginFilterNotImplemented as not_found_error:
    # We are expecting this exception
    print("got {}".format(not_found_error), file=sys.stderr)
    #raise not_found_error


  # Test that real plugin was registered
  plugin_whisper = vcon.filter_plugins.FilterPluginRegistry.get("whisper")
  assert(plugin_whisper is not None)
  assert(plugin_whisper.import_plugin() == True)

  # Verify whisper is the default transcribe type filter plugin
  assert(vcon.filter_plugins.FilterPluginRegistry.get_type_default_name("transcribe") == "whisper")

  in_vcon = vcon.Vcon()
  options = {}
  try:
    out_vcon = in_vcon.filter("doesnotexist", **options)
    raise Exception("Expected not to find plugin and throw exception")

  except vcon.filter_plugins.PluginFilterNotRegistered as not_reg_error:
    print(not_reg_error, file=sys.stderr)

  import tests.bar_reg

  v2 = vcon.Vcon()

  try:
    v2.barp()
    raise Exception("expect exception as filter plugin bar trys to import a non-existant package")

  except vcon.filter_plugins.PluginModuleNotFound as fp_no_mod_error:
    # should get here
    print("got {}".format(fp_no_mod_error))

