# -*- coding: utf-8 -*-

# Copyright (C) 2014-2015 emijrp <emijrp@gmail.com>
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
import string
import sys

def loadCurrentEventsCSV(csvfile):
    c = 0
    f = csv.reader(open(csvfile, 'r'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    l = []
    for row in f:
        if c == 0:
            c += 1
            continue
        
        d = {
            'page_id': int(row[0]),
            'page_namespace': int(row[1]),
            'page_title': row[2],
            'page_creator': row[3],
            'page_creator_type': row[4],
            'page_creation_date': row[5],
            'it_rev_id': int(row[6]),
            'it_rev_timestamp': row[7],
            'it_rev_username': row[8],
            'it_rev_comment': row[9],
            'rt_rev_id': row[10] and int(row[10]) or '',
            'rt_rev_timestamp': row[11],
            'rt_rev_username': row[12],
            'rt_rev_comment': row[13],
            'tag_type': row[14],
            'tag_string': row[15],
            'tag_time_since_creation': row[16],
            'tag_duration': row[17],
            'tag_edits': int(row[18]),
            'tag_distinct_editors': int(row[19]),
            'diff_links': int(row[20]),
            'diff_extlinks': int(row[21]),
            'diff_refs':  int(row[22]),
            'diff_templates': int(row[23]),
        }
        l.append(d)
        c += 1
    
    return l

def loadPagesCSV(csvfile):
    c = 0
    f = csv.reader(open(csvfile, 'r'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    l = []
    for row in f:
        if c == 0:
            c += 1
            continue

        d = {
            'page_id': int(row[0]), 
            'page_namespace': int(row[1]), 
            'page_title': row[2], 
            'page_creation_date': row[3], 
            'page_creator': row[4], 
            'page_is_redirect': row[5]=='True' and True or False, 
        }
        l.append(d)
        c += 1
    
    return l

def main():
    if len(sys.argv) == 3:
        dumpwiki = sys.argv[1]
        dumpdate = sys.argv[2]
    else:
        print('Missing wiki and date: python script.py eswiki 20140509')
        sys.exit()
    
    #currentevents csv
    csvfiles = glob.glob("currentevents-%s-%s.csv.*" % (dumpwiki, dumpdate))
    csvfiles.sort()
    currentevents = []
    for csvfile in csvfiles:
        print('Loading',csvfile)
        currentevents += loadCurrentEventsCSV(csvfile)
    print('Loaded',len(currentevents),'current events')
    
    #pages csv
    csvfiles = glob.glob("newpages-%s-%s.csv.*" % (dumpwiki, dumpdate))
    csvfiles.sort()
    pages = []
    for csvfile in csvfiles:
        print('Loading',csvfile)
        pages += loadPagesCSV(csvfile)
    print('Loaded',len(pages),'pages')
    
    num2namespace = {
        'eswiki': {0:'Principal', 104:'Anexo'}, 
    }
    namespaces = list(set([currentevent['page_namespace'] for currentevent in currentevents]))
    namespaces.sort()
    d = {
        'dumpdate': dumpdate, 
        'namespaces': ', '.join(['%d (%s)' % (nm, num2namespace[dumpwiki][nm]) for nm in namespaces]), 
        'totalcurrentevents': len(currentevents), 
        'totalcurrenteventspages': len(set([currentevent['page_id'] for currentevent in currentevents])), 
        'totalnamespaces': len(namespaces), 
        'totalusefulpages': sum([not page['page_is_redirect'] for page in pages]), 
        'totalpages': len(pages), 
        'totalredirects': sum([page['page_is_redirect'] for page in pages]), 
        'wiki': dumpwiki, 
        'wikilang': dumpwiki.split('wiki')[0], 
    }
    #extra calculations
    d['redirectspercent'] = round(d['totalredirects']/(d['totalpages']/100), 1)
    d['usefulpagespercent'] = round(d['totalusefulpages']/(d['totalpages']/100), 1)

    html = string.Template("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html lang="en" dir="ltr" xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Current events ($wiki, $dumpdate)</title>
    <meta http-equiv="content-type" content="text/html;charset=utf-8" />
</head>
<body>
    <h1>Current events ($wiki, $dumpdate)</h1>
    
    <p>Este análisis corresponde a <b><a href="https://$wikilang.wikipedia.org">$wiki</a></b> con la fecha <b>$dumpdate</b>. 
    
    <p>Resumen general:</p>
    <ul>
        <li>Se han analizado <b>$totalnamespaces</b> espacios de nombres: $namespaces.</li>
        <li>Se han encontrado <b>$totalusefulpages</b> páginas de contenido y <b>$totalredirects</b> redirecciones. En total <b>$totalpages</b> páginas.</li>
        <ul>
            <li>El <b>$usefulpagespercent%</b> son páginas de contenido y el <b>$redirectspercent%</b> son redirecciones.</li>
        </ul>
        <li>Se han encontrado <b>$totalcurrentevents</b> eventos de actualidad repartidos en <b>$totalcurrenteventspages</b> páginas.</li>
    </ul>
</body>
</html>
""")
    
    html = html.substitute(d)
    
    f = open('index.html', 'w')
    f.write(html)
    f.close()
    
if __name__ == '__main__':
    main()
