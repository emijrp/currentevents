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
    
    months = {}
    
    #newpages
    csvfiles = glob.glob("newpages-%s-%s.csv.*" % (dumpwiki, dumpdate))
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
            page_creation_date = row[3]
            page_creator = row[4]
            page_is_redirect = row[5] == 'True' and True or False
            
            if page_namespace != 0:
                continue
            if page_is_redirect:
                continue
            
            month = page_creation_date[:7]
            if months.has_key(month):
                months[month]['newpages'].add(page_id)
            else:
                months[month] = {'newpages': set([]), 'currentevents': set([]), 'other': set([])}
            
            c += 1
    
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
            
            month = page_creation_date[:7]
            if ',' not in tag_time_since_creation or re.search(ur"(?im)^[1-9] days?,", tag_time_since_creation):
                #Creado por noticia
                months[month]['currentevents'].add(page_id)
            else:
                #Creado al azar
                months[month]['other'].add(page_id)
            c += 1
    
    months_list = [[k, v] for k, v in months.items()]
    months_list.sort()
    
    resultsfile = 'articlespermonth-%s-%s.csv' % (dumpwiki, dumpdate)
    g = open(resultsfile, 'w')
    g.write('month|newpages_never_tagged|tagged_before_10_days|tagged_after_10_days\n')
    g.close()
    
    for month, props in months_list:
        newpagesnum = len(props['newpages'])
        currenteventsnum = len(props['currentevents'])
        othernum = len(props['other']) 
        g = csv.writer(open(resultsfile, 'a'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        g.writerow([month, newpagesnum-(currenteventsnum+othernum), currenteventsnum, othernum])
    
    print 'Results written in', resultsfile

if __name__ == '__main__':
    main()
