import vcon.filter_plugins

vcon.filter_plugins.FilterPluginRegistry.register("barp", "tests.bar", "Foo", "Does bar")


#print(vcon.filter_plugins.FilterPluginRegistry.get_names())

