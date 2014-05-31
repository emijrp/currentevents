# -*- coding: utf-8 -*-

# Copyright (C) 2014 emijrp <emijrp@gmail.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import csv
import glob
import os
import re
import sys

def main():
    if len(sys.argv) == 3:
        dumpwiki = sys.argv[1]
        dumpdate = sys.argv[2]
    else:
        print 'Missing wiki and date: python script.py eswiki 20140509'
        sys.exit()
    
    days = {0:0}
    
    #currentevents
    csvfiles = glob.glob("currentevents-%s-%s.csv.*" % (dumpwiki, dumpdate))
    csvfiles.sort()
    for csvfile in csvfiles:
        c = 0
        f = csv.reader(open(csvfile, 'r'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in f:
            if c == 0:
                c += 1
                continue
            
            page_id = int(row[0])
            page_namespace = int(row[1])
            page_title = row[2]
            page_creator = row[3]
            page_creator_type = row[4]
            page_creation_date = row[5]
            it_rev_id = int(row[6])
            it_rev_timestamp = row[7]
            it_rev_username = row[8]
            it_rev_comment = row[9]
            rt_rev_id = row[10] and int(row[10]) or ''
            rt_rev_timestamp = row[11]
            rt_rev_username = row[12]
            rt_rev_comment = row[13]
            tag_type = row[14]
            tag_string = row[15]
            tag_time_since_creation = row[16]
            tag_duration = row[17]
            tag_edits = int(row[18])
            tag_distinct_editors = int(row[19])
            
            if re.search(ur'day', tag_time_since_creation):
                numdays = int(tag_time_since_creation.split(' day')[0])
                if not days.has_key(numdays):
                    days[numdays] = 0
                days[numdays] += 1
            else:
                days[0] += 1
            
            c += 1
    
    days_list = []
    for k, v in days.items():
        days_list.append([k, v])
    days_list.sort()
    
    resultsfile = 'tagtimesincecreation-%s-%s.csv' % (dumpwiki, dumpdate)
    g = open(resultsfile, 'w')
    g.write('days|pages|acumulated\n')
    g.close()
    
    acum = 0
    for k, v in days_list:
        acum += v
        g = csv.writer(open(resultsfile, 'a'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        g.writerow([k, v, acum])
    
    print 'Results written in', resultsfile

if __name__ == '__main__':
    main()
