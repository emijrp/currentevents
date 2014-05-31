#!/bin/bash

#$1 is wiki: eswiki, enwiki,...
#$2 is date: 20140509, 20140502,...
#$3 is format: bz2, 7z, ...

shopt -s nullglob
dumps=(/data/project/currentevents/dumps/$1/$2/$1-$2-pages-meta-history*.xml*.$3)
c=1

for dump in "${dumps[@]}"
do
    jsub -N $1$c -mem 5000m /bin/bash /data/project/currentevents/code/currentevents2.sh $dump $c
    c=$[$c +1]
done
