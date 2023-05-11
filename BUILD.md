# Build Instructions

  + [Building Vcon core package](#building-vcon-core-package)
  + [Building the conserver package](#building-the-conserver-package)

## Building Vcon core package

Make sure python build and twine packages are installed:

    pip3 install --upgrade build twine

Update the version number in vcon/vcon/__init__.py

Be sure to clean out the dist directory:

    rm dist/*

In vcon directory (root containing setup.py and vcon sub-directory):

    python3 -m build

This creates sub-directory dist containing (x.x in the names below represents the version number):

  * vcon-x.x-py3-none-any.whl
  * vcon-x.x.tar.gz

Push the package install files up to the pypi repo.

For the test repo:

    python3 -m twine upload --repository testpypi dist/*

For the real/public repo:

    python3 -m twine upload dist/*

Commit all of the changes and tag the build release:

    git tag -a vcon_x.x [xxxxx_commit_SHA] -m "Vcon pypi release"

## Building the conserver package

TBD

