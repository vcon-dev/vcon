import vcon.filter_plugins

vcon.filter_plugins.FilterPluginRegistry.register("foop", "tests.foo", "Foo", "Does foo")


#print(vcon.filter_plugins.FilterPluginRegistry.get_names())

