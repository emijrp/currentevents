#!/bin/bash

#bash currentevents.sh eswiki 20140509 4

for i in {1..$3}
do
    jsub -N $1$i /bin/bash /data/project/currentevents/code/currentevents2.sh $1 $2 $i
done
