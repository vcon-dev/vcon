
PIP_LAYER_PACKAGES= python-jose cryptography vcon

PIP_LAYER_PACKAGES_ZIPS = $(addprefix layers/,$(PIP_LAYER_PACKAGES:=.zip))

LAYER_PATH = "python/lib/python3.8/site-packages"
LAYER_PATH_ROOT = "python"

layers: ${PIP_LAYER_PACKAGES_ZIPS}
	@echo "layers: ${PIP_LAYER_PACKAGES_ZIPS}"

layers/%.zip:
	@echo "Making $@"
	@if [ ! -d "layers" ]; then mkdir layers; fi
	@(cd /tmp; mkdir -p ${LAYER_PATH}; pip3 install $* -t ${LAYER_PATH} > /dev/null; zip $*.zip -r ${LAYER_PATH_ROOT} > /dev/null; rm -rf ${LAYER_PATH_ROOT})
	@mv /tmp/$*.zip layers

layers/vcon.zip: vcon vcon/__init__.py
	@echo "Making $@"
	@if [ ! -d "layers" ]; then mkdir layers; fi
	@mkdir -p /tmp/${LAYER_PATH}
	@cp -rp vcon /tmp/${LAYER_PATH}
	@(cd /tmp; zip vcon.zip -r ${LAYER_PATH_ROOT} > /dev/null; rm -rf ${LAYER_PATH_ROOT})
	@mv /tmp/vcon.zip layers

test:
	pytest -v
