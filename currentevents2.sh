#!/bin/bash

source /data/project/currentevents/code/bin/activate
time python /data/project/currentevents/code/currentevents.py $1 $2
deactivate
