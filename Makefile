.PHONY: all build test clean
.SILENT: test

all: build

clean:
	python setup.py clean
	-rm -rf dist/*
	-rmdir dist
	-rm -rf build/*
	-rmdir build
	find . -name *.pyc -type f -exec rm '{}' \;
	-rm -rf *.egg-info

test:
	python setup.py test

sdist:
	python setup.py sdist

build:
	python setup.py bdist

install:
	python setup.py install
