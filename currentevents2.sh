#!/bin/bash

source /data/project/currentevents/code/bin/activate
time python /data/project/currentevents/code/currentevents.py /data/project/currentevents/code/$1-$2-pages-meta-history$3.xml.bz2 $3
deactivate
