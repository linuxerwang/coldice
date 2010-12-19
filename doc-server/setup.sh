#!/bin/sh

python setup.py bdist_egg --exclude-source-files
chmod a+x dist/*.egg

