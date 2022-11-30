from __future__ import annotations
import importlib
import typing
import sys

# This package is dependent upon the vcon package only for typing purposes.
# This creates a circular dependency which we avoid by importing annotations
# above and importing vcon only if typing.TYPE_CHECKING
if typing.TYPE_CHECKING:
  from vcon import Vcon

class PluginModuleNotFound(Exception):
  """ Thrown when plugin modeule fails to load """

class PluginClassNotFound(Exception):
  """ Thrown when plugin class is not found in plugin module """

class FilterPlugin:
  def __init__(self, options: dict):
    pass

  def filter(self, in_vcon: Vcon, options: dict = {}) -> Vcon:
    raise Exception("{}.filter not implemented".format(type(self)))

  def uninit(self):
    pass

class FilterPluginRegistration:
  def __init__(self, name: str, module_name: str, class_name: str, description: str):
    self.name = name
    self._module_name = module_name
    self._module_load_attempted = False
    self._module_not_found = False
    self._class_not_found = False
    self._class_name = class_name
    self.description = description
    self._plugin = None

  def import_plugin(self, options: dict = {}) -> bool:
    succeed = False
    if(not self._module_load_attempted):
      try:
        print("importing: {} for plugin: {}".format(self._module_name, self.name))
        module = importlib.import_module(self._module_name)
        self._module_load_attempted = True
        self._module_not_found = False

        try:
          class_ = getattr(module, self._class_name)
          self._plugin = class_(options)
          self._class_not_found = False
          succeed = True

        except AttributeError as ae:
          print(ae, file=sys.stderr)
          self._class_not_found = True

      except ModuleNotFoundError as mod_error:
        print(mod_error, file=sys.stderr)
        self._module_not_found = True

    elif(slef._plugin is not None):
      succeed = True

    return(succeed)

  def plugin(self, options : dict = {}) -> FilterPlugin:
    if(not self._module_load_attempted):
      self.import_plugin(options)

    return(self._plugin)

  def filter(self, in_vcon : vcon.Vcon, options : dict = {}) -> vcon.Vcon:
    if(not self._module_load_attempted):
      self.import_plugin(options)

    if(self._module_not_found is True):
      message = "plugin: {} not loaded as module: {} was not found".format(self.name, self._module_name)
      raise PluginModuleNotFound(message)

    elif(self._class_not_found is True):
      message = "plugin: {} not loaded as class: {} not found in module: {}".format(self.name, self._class_name, self._module_name)
      raise PluginClassNotFound(message)

    plugin = self.plugin(options)
    if(plugin is None):
      raise Exception("plugin: {} from class: {} module: {} load failed".format(self.name, self._class_name, self._module_name))
    else:
      return(plugin.filter(options))

class FilterPluginRegistry:
  _registry: typing.Dict[str, FilterPluginRegistration] = {}


  @staticmethod
  def __add_plugin(plugin: FilterPluginRegistration, replace=False):
    if(FilterPluginRegistry._registry.get(plugin.name) is None or replace):
     FilterPluginRegistry._registry[plugin.name] = plugin
    else:
      raise Exception("Plugin {} already exists".format(plugin.name))


  @staticmethod
  def register(name: str, module_name: str, class_name: str, description: str, replace: bool = False):
    """
    """
    entry = FilterPluginRegistration(name, module_name, class_name, description)
    FilterPluginRegistry.__add_plugin(entry, replace)

  @staticmethod
  def get(name: str) -> FilterPluginRegistration:
    """
    Returns registration for named plugin
    """
    return(FilterPluginRegistry._registry.get(name, None))

  @staticmethod
  def get_names() -> list[str]:
    """
    Returns list of plugin names
    """
    return(FilterPluginRegistry._registry.keys())

class TranscriptionFilter(FilterPlugin):
  def __init__(self, options: dict):
    super().__init__(options)

  def iterateDialogs(self, in_vcon: Vcon, scope: str ="new"):
    """
    Iterate through the dialogs in the given vCon

    Parameters:
      scope = "all", "new"
         "new" = dialogs containing a recording for which there is no transcript
         "all" = all dialogs which contain a recording
    """

