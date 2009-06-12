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
	LD_LIBRARY_PATH=$(EPATH)/lib \
	PYTHONPATH=$(EPATH)/lib/python2.5/site-packages:applications:core:services \
	./scripts/paroli

.PHONY: edj
edj:
	cd scripts && \
	PATH=$(PATH):$(EPATH)/bin \
	LD_LIBRARY_PATH=$(EPATH)/lib \
	PYTHONPATH=$(EPATH)/lib/python2.5/site-packages:../python-pyneo/ \
	./build.sh

.PHONY: dbg
dbg: clean
	rsync --verbose --archive --delete * root@$(HOST):/usr/share/paroli/.

.PHONY: clean
clean:
	find . -name \*.pyo -o -name \*.pyc | xargs rm -f
	rm -rf dist build docs

.PHONY: docs
docs: docs/index.html

docs/index.html: Makefile
	mkdir -p docs
	LD_LIBRARY_PATH=$(EPATH)/lib \
	PYTHONPATH=$(EPATH)/lib/python2.5/site-packages:applications:core:services \
	epydoc \
		--css=data/epydoc.css \
		--debug \
		--docformat=restructuredtext \
		--graph=classtree \
		--graph-font-size=32 \
		--graph-font='Vera' \
		--html \
		--include-log \
		--name='paroli - documentation' \
		--navlink=Home \
		--no-imports \
		--no-private \
		--no-sourcecode \
		--output=docs \
		--quiet \
		--simple-term \
		--url=http://www.paroli-project.org/ \
		core/* services/* applications/*

