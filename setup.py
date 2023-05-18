import os
import sys
import setuptools

requires = []

#print("CWD: {}".format(os.getcwd()), file=sys.stderr)
#print("files in CWD: {}".format(os.listdir(os.getcwd())), file=sys.stderr)

with open("vcon/docker_dev/pip_package_list.txt") as core_file:
  line = core_file.readline()
  while line:
    line=line.strip()
    if( len(line) > 0 and line[0] != '#'):
      requires.append(line)
    line = core_file.readline()

print("vcon package dependencies: {}".format(requires), file=sys.stderr)

def get_version()-> str:
  """ 
  This is kind of a PITA, but the build system barfs when we import vcon here
  as depenencies are not installed yet in the vritual environment that the 
  build creates.  Therefore we cannot access version directly from vcon/__init__.py.
  So I have hacked this means of parcing the version value rather than
  de-normalizing it and having it set in multiple places.
  """ 
  with open("vcon/__init__.py") as core_file:
    line = core_file.readline()
    while line:
      if(line.startswith("__version__")):
        variable, equals, version = line.split()
        assert(variable == "__version__")
        assert(equals == "=")
        version = version.strip('"')
        version_double = float(version)
        assert(version_double >= 0.01)
        assert(version_double < 10.0)
        break

      line = core_file.readline()

  return(version)

__version__ = get_version()

setuptools.setup(
  name='vcon',
  version=__version__,
  #version="0.1",
  description='vCon container manipulation package',
  url='http://github.com/von-dev/vcon',
  author='Dan Petrie',
  author_email='dan.vcon@sipez.com',
  license='MIT',
  packages=['vcon', 'vcon.filter_plugins', 'vcon.filter_plugins.impl'],
  data_files=[
    ("vcon", ["vcon/docker_dev/pip_package_list.txt"])],
  python_requires=">=3.6",
  tests_require=['pytest', 'pytest-asyncio', 'pytest-dependency'],
  install_requires=requires,
  scripts=['vcon/bin/vcon'],
  # entry_points={
  #   'console_scripts': [
  #     'vcon = vcon:cli:main',
  #     ]
  #   }
  zip_safe=False)

