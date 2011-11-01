#!/bin/sh -ex

if [ ! -d epubcheck ]
then
    mkdir epubcheck
    cd epubcheck
    curl -s http://epubcheck.googlecode.com/files/epubcheck-1.2.zip -o epubcheck-1.2.zip
    unzip epubcheck-1.2.zip
    cd ..
fi

python build.py
java -jar epubcheck/epubcheck-1.2.jar Revolution_in_The_Valley.epub
