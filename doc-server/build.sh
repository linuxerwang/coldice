#!/bin/sh

DEB_TOP="debian"
DOCSERVER_TOP="$DEB_TOP/usr/share/docserver"

mkdir -p DOCSERVER_TOP
cp -r src/ds $DOCSERVER_TOP/
python -m compileall $DOCSERVER_TOP
for one in `find $DOCSERVER_TOP | grep "\.py$"`;
do
    rm $one
done
fakeroot dpkg -b debian .

