#!/usr/bin/env make -f
#HOST=murphy
#HOST=om-gta01
HOST=om-gta02
EPATH=/opt/e17

.PHONY: all
all:
	PATH=$(PATH):$(EPATH)/bin \
	LD_LIBRARY_PATH=$(EPATH)/lib \
	PYTHONPATH=$(EPATH)/lib/python2.5/site-packages:../python-pyneo/ \
	./setup.py bdist

.PHONY: run
run:
	./scripts/paroli

.PHONY: dbg
dbg: clean
	rsync --verbose --archive --delete * root@$(HOST):/usr/share/paroli/.

.PHONY: clean
clean:
	find . -name \*.pyo -o -name \*.pyc | xargs rm -f
	rm -rf dist build

