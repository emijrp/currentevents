#!/bin/bash

source /data/project/currentevents/code/bin/activate
time python /data/project/currentevents/code/currentevents.py /data/project/currentevents/code/eswiki-20140509-pages-meta-history$1.xml.bz2 $1
deactivate
