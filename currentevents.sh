#!/bin/bash

for i in {1..4}
do
    jsub -N eswiki$i -mem 10000m /bin/bash /data/project/currentevents/code/currentevents2.sh $i
done
