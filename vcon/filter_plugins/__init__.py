""" Vcon module providing frameword for filter plugins which take a Von in and provide a Vcon output """
from __future__ import annotations
import importlib
import typing
import sys
import os
import traceback
import logging
import pythonjsonlogger.jsonlogger


# This package is dependent upon the vcon package only for typing purposes.
# This creates a circular dependency which we avoid by importing annotations
# above and importing vcon only if typing.TYPE_CHECKING
if typing.TYPE_CHECKING:
  from vcon import Vcon

# This is cloned from vcon package as we cannot import vcon here due to
# cyclical import.
def build_logger(name : str) -> logging.Logger:
  logger = logging.getLogger(name)

  log_config_filename = "./logging.conf"
  if(os.path.isfile(log_config_filename)):
    logging.config.fileConfig(log_config_filename)
    #print("got logging config", file=sys.stderr)
  else:
    logger.setLevel(logging.DEBUG)

    # Output to stdout WILL BREAK the Vcon CLI.
    # MUST use stderr.
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    formatter = pythonjsonlogger.jsonlogger.JsonFormatter( "%(timestamp)s %(levelname)s %(message)s ", timestamp=True)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

  return(logger)
logger = build_logger(__name__)

class PluginModuleNotFound(Exception):
  """ Thrown when plugin modeule fails to load """

class PluginClassNotFound(Exception):
  """ Thrown when plugin class is not found in plugin module """

class PluginFilterNotImplemented(Exception):
  """ Thrown when plugin modeule and class are found, but methods are not implemented on filter"""

class PluginFilterNotRegistered(Exception):
  """ Thrown when plugin is not found in the FilterPluginRegistry """

class PluginFilterAlreadyRegistered(Exception):
  """ Thrown when plugin already exists in the FilterPluginRegistry """

class FilterPlugin:
  """ Abstract Vcon filter plugin class.  Implementations derive from this clss and must implement the filter method """
  def __init__(self, **options):
    pass

  def filter(self, in_vcon: Vcon, **options) -> Vcon:
    """
    Abstract method which performs an operation on an input Vcon and 
    provides the modified Vcon as output.

    Parameters:
      in_vcon (vcon.Vcon) - input Vcon upon which an operation is to be performed by the plugin.
      options (kwargs) - opaque options to the filter method/opearation

    Returns:
      vcon.Vcon - the modified Vcon
    """
    raise PluginFilterNotImplemented("{}.filter not implemented".format(type(self)))

  def __del__(self):
    """ Teardown/uninitialization method for the plugin """
    print("deleting {}".format(self.__class__))

class FilterPluginRegistration:
  """ Class containing info and heloer methods on the registration for a single named plugin filter """
  def __init__(self, name: str, module_name: str, class_name: str, description: str):
    self.name = name
    self._module_name = module_name
    self._module_load_attempted = False
    self._module_not_found = False
    self._class_not_found = False
    self._class_name = class_name
    self.description = description
    self._plugin : typing.Union[FilterPlugin, None] = None

  def import_plugin(self, **options) -> bool:
    """
    Import the package which contains the implementation for the filter
    plugin and instantiate the plugin class.

    filter plugins are registered and later if used, they are imported.
    When registered, a filter plugin has a name, an implementation module,
    and a class which gets instantiated upon import of the package.

    Parameters:
      options (kwargs) - options input to the plugin class constructor

    Returns:
      True/False if the plugin module imported successfully and the
        class was instantiated.
    """
    succeed = False
    if(not self._module_load_attempted):
      try:
        logger.info("importing: {} for registered filter plugin: {}".format(self._module_name, self.name))
        module = importlib.import_module(self._module_name)
        self._module_load_attempted = True
        self._module_not_found = False

        try:
          class_ = getattr(module, self._class_name)
          self._plugin = class_(**options)
          self._class_not_found = False
          succeed = True

        except AttributeError as ae:
          logger.warning(ae)
          self._class_not_found = True

      except ModuleNotFoundError as mod_error:
        logger.warning(mod_error)
        logger.warning(traceback.format_exc(limit=-1))
        self._module_not_found = True

    elif(self._plugin is not None):
      succeed = True

    return(succeed)

  def plugin(self, **options) -> typing.Union[FilterPlugin, None]:
    """ Return the plugin filter class for this registration """
    if(not self._module_load_attempted):
      self.import_plugin(**options)

    return(self._plugin)

  def filter(self, in_vcon : vcon.Vcon, **options) -> vcon.Vcon:
    if(not self._module_load_attempted):
      self.import_plugin(**options)

    if(self._module_not_found is True):
      message = "plugin: {} not loaded as module: {} was not found".format(self.name, self._module_name)
      raise PluginModuleNotFound(message)

    if(self._class_not_found is True):
      message = "plugin: {} not loaded as class: {} not found in module: {}".format(self.name, self._class_name, self._module_name)
      raise PluginClassNotFound(message)

    plugin = self.plugin(**options)
    if(plugin is None):
      raise Exception("plugin: {} from class: {} module: {} load failed".format(self.name, self._class_name, self._module_name))

    return(plugin.filter(in_vcon, **options))

class FilterPluginRegistry:
  """ class/scope for Vcon filter plugin registrations and defaults for plugin types """
  _registry: typing.Dict[str, FilterPluginRegistration] = {}
  _defaults: typing.Dict[str, str] = {}

  @staticmethod
  def __add_plugin(plugin: FilterPluginRegistration, replace=False):

    name_registered = FilterPluginRegistry._registry.get(plugin.name)
    if(name_registered is None):
      # TODO: fix circular import dependency problem
      #import vcon
      #if(vcon.Vcon.attribute_exists(plugin.name)):
      #  raise AttributeError("{} is a reserved name already used as a Vcon class or instance name".format(plugin.name))
      pass

    if(name_registered is None or replace):
         
      FilterPluginRegistry._registry[plugin.name] = plugin
    else:
      raise PluginFilterAlreadyRegistered("Plugin {} already registered".format(plugin.name))


  @staticmethod
  def register(name: str, module_name: str, class_name: str, description: str, replace: bool = False) -> None:
    """
    Register a named filter plugin.

    Parameters:
      name (str) - the name to register the plugin

      module_name (str) - the module name to import where the plugin class is implmented

      class_name (str) - the class name for the plugin implementation in the named module

      description (str) - a text description of what the plugin does

      replace (bool) - if True replace the already registered plugin of the same name
                       if False throw an exception if a plugin of the same name is already register
    """
    logger.info("Registering FilterPlugin: {}".format(locals()))
    entry = FilterPluginRegistration(name, module_name, class_name, description)
    FilterPluginRegistry.__add_plugin(entry, replace)


  @staticmethod
  def get(name: str) -> FilterPluginRegistration:
    """
    Returns registration for named plugin
    """
    plugin_reg = FilterPluginRegistry._registry.get(name, None)
    if(plugin_reg is None):
      raise PluginFilterNotRegistered("Filter plugin {} is not registered".format(name))

    return(plugin_reg)

  @staticmethod
  def get_names() -> typing.List[str]:
    """
    Returns list of plugin names
    """
    return(FilterPluginRegistry._registry.keys())

  @staticmethod
  def set_type_default_name(plugin_type: str, name: str) -> None:
    """ Set the default filter name for the given filter type """
    FilterPluginRegistry._defaults[plugin_type] = name

  @staticmethod
  def get_type_default_name(plugin_type: str) -> typing.Union[str, None]:
    """ Get the default plugin name for the given filter type """
    return(FilterPluginRegistry._defaults.get(plugin_type, None))

  @staticmethod
  def get_types() -> typing.List[str]:
    """
    Get the set of FilterPlugin types.

    Returns:
      list(str) - names of all the types for which a default is set.
    """
    return(FilterPluginRegistry._defaults.keys())

  @staticmethod
  def get_type_default_plugin(plugin_type: str) -> typing.Union[FilterPluginRegistration, None]:
    """ Get the default FilterPlauginRegistration for the named filter type """
    if(not isinstance(plugin_type, str)):
      raise AttributeError("plugin_type argument should be a string, not {}".format(type(plugin_type)))

    name = FilterPluginRegistry.get_type_default_name(plugin_type)
    if(name is None):
      raise PluginFilterNotRegistered("Filter plugin default type name {} is not set".format(plugin_type))
    return(FilterPluginRegistry.get(name))

class TranscriptionFilter(FilterPlugin):
  # TODO abstraction of transcription filters, iterates through dialogs
  def __init__(self, **options):
    super().__init__(**options)

  def iterateDialogs(self, in_vcon: Vcon, scope: str ="new"):
    """
    Iterate through the dialogs in the given vCon

    Parameters:
      scope = "all", "new"
         "new" = dialogs containing a recording for which there is no transcript
         "all" = all dialogs which contain a recording
    """

