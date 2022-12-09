import vcon.filter_plugins

class Foo(vcon.filter_plugins.FilterPlugin):
  def __init__(self, **options):
    super().__init__(**options)
    print("foo plugin created with options: {}".format(options))

