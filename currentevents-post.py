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
    d = {}
    for row in f:
        if c == 0:
            c += 1
            continue
        
        d[int(row[6])] = {
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
            'diff_len': int(row[20]),
            'diff_links': int(row[21]),
            'diff_extlinks': int(row[22]),
            'diff_refs':  int(row[23]),
            'diff_templates': int(row[24]),
            'diff_images': int(row[25]),
        }
        c += 1
    
    return d

def loadPagesCSV(csvfile):
    c = 0
    f = csv.reader(open(csvfile, 'r'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    d = {}
    for row in f:
        if c == 0:
            c += 1
            continue

        d[int(row[0])] = {
            'page_id': int(row[0]), 
            'page_namespace': int(row[1]), 
            'page_title': row[2], 
            'page_creation_date': row[3], 
            'page_creator': row[4], 
            'page_is_redirect': row[5] == 'True' and True or False, 
        }
        c += 1
    
    return d

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
    currentevents = {}
    for csvfile in csvfiles:
        print('Loading',csvfile)
        d = loadCurrentEventsCSV(csvfile)
        for k, v in d.items():
            currentevents[k] = v
    print('Loaded',len(currentevents.items()),'current events')
    
    #pages csv
    csvfiles = glob.glob("pages-%s-%s.csv.*" % (dumpwiki, dumpdate))
    csvfiles.sort()
    pages = {}
    for csvfile in csvfiles:
        print('Loading',csvfile)
        d = loadPagesCSV(csvfile)
        for k, v in d.items():
            pages[k] = v
    print('Loaded',len(pages.items()),'pages')
    
    #dict for stats
    num2namespace = {
        'eswiki': {0:'Principal', 104:'Anexo'}, 
    }
    namespaces = list(set([v['page_namespace'] for k, v in currentevents.items()]))
    namespaces.sort()
    d = {
        'dumpdate': dumpdate, 
        'namespaces': ', '.join(['%d (%s)' % (nm, num2namespace[dumpwiki][nm]) for nm in namespaces]), 
        'newestcurrenteventtitle': '', 
        'newestcurrenteventdate': '2000-01-01T00:00:00Z', 
        'newestcurrenteventuser': '', 
        'newestpagetitle': '', 
        'newestpagecreationdate': '2000-01-01T00:00:00Z', 
        'newestpagecreator': '', 
        'oldestcurrenteventtitle': '', 
        'oldestcurrenteventdate': '2099-01-01T00:00:00Z', 
        'oldestcurrenteventuser': '', 
        'oldestpagetitle': '', 
        'oldestpagecreationdate': '2099-01-01T00:00:00Z', 
        'oldestpagecreator': '', 
        'totalcurrentevents': len(currentevents.keys()), 
        'totalcurrenteventspages': len(set([v['page_id'] for k, v in currentevents.items()])), 
        'totalnamespaces': len(namespaces), 
        'totalusefulpages': sum([not v['page_is_redirect'] for k, v in pages.items()]), 
        'totalpages': len(pages), 
        'totalredirects': sum([v['page_is_redirect'] for k, v in pages.items()]), 
        'wiki': dumpwiki, 
        'wikilang': dumpwiki.split('wiki')[0], 
    }
    #extra calculations
    d['redirectspercent'] = round(d['totalredirects']/(d['totalpages']/100), 1)
    d['usefulpagespercent'] = round(d['totalusefulpages']/(d['totalpages']/100), 1)
    
    #csvlinks
    d['csvlinks'] = ''
    
    #oldest & newest current events
    for k, v in currentevents.items():
        if v['it_rev_timestamp'] < d['oldestcurrenteventdate']:
            d['oldestcurrenteventtitle'] = v['page_title']
            d['oldestcurrenteventdate'] = v['it_rev_timestamp']
            d['oldestcurrenteventrevid'] = v['it_rev_id']
            d['oldestcurrenteventuser'] = v['it_rev_username']

    for k, v in currentevents.items():
        if v['it_rev_timestamp'] > d['newestcurrenteventdate']:
            d['newestcurrenteventtitle'] = v['page_title']
            d['newestcurrenteventdate'] = v['it_rev_timestamp']
            d['newestcurrenteventrevid'] = v['it_rev_id']
            d['newestcurrenteventuser'] = v['it_rev_username']

    #oldest & newest pages
    for k, v in pages.items():
        if v['page_creation_date'] < d['oldestpagecreationdate']:
            d['oldestpagetitle'] = v['page_title']
            d['oldestpagecreationdate'] = v['page_creation_date']
            d['oldestpagecreator'] = v['page_creator']

    for k, v in pages.items():
        if v['page_creation_date'] > d['newestpagecreationdate']:
            d['newestpagetitle'] = v['page_title']
            d['newestpagecreationdate'] = v['page_creation_date']
            d['newestpagecreator'] = v['page_creator']
    
    #stats by year
    stats_by_year = {}
    for k, v in currentevents.items():
        year = int(v['it_rev_timestamp'].split('-')[0])
        if year in stats_by_year:
            stats_by_year[year]['currentevents'] += 1
            stats_by_year[year]['articles'].add(v['page_id'])
        else:
            stats_by_year[year] = {'currentevents': 1, 'articles': set([v['page_id']])}
    stats_by_year = [[k, v] for k, v in stats_by_year.items()]
    stats_by_year.sort()
    stats_by_year = '\n'.join(["<tr><td>{0}</td><td>{1}</td><td>{2}</td></tr>".format(k, v['currentevents'], len(v['articles'])) for k, v in stats_by_year])
    d['stats_by_year'] = "<table border=1 style='text-align: center;'>\n<th>Año</th><th>Eventos</th><th>Artículos</th>\n{0}\n</table>".format(stats_by_year)
    
    html = string.Template("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html lang="en" dir="ltr" xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Current events ($wiki, $dumpdate)</title>
    <meta http-equiv="content-type" content="text/html;charset=utf-8" />
</head>
<body>
    <h1>Current events ($wiki, $dumpdate)</h1>
    
    <p>Este análisis corresponde a <b><a href="https://$wikilang.wikipedia.org">$wiki</a></b> con la fecha <b>$dumpdate</b>.
    
    <p>Se ha generado en X horas.</p>
    <ul>
        $csvlinks
    </ul>
    
    <p>Resumen general:</p>
    <ul>
        <li>Se han analizado <b>$totalnamespaces</b> espacios de nombres: $namespaces.</li>
        <li>Se han encontrado <b>$totalusefulpages</b> páginas de contenido y <b>$totalredirects</b> redirecciones. En total <b>$totalpages</b> páginas.</li>
        <ul>
            <li>El <b>$usefulpagespercent%</b> son páginas de contenido y el <b>$redirectspercent%</b> son redirecciones.</li>
            <li>La página más antigua es <a href="https://$wikilang.wikipedia.org/wiki/$oldestpagetitle">$oldestpagetitle</a>, creada por <a href="https://$wikilang.wikipedia.org/wiki/User:$oldestpagecreator">$oldestpagecreator</a> (<a href="https://$wikilang.wikipedia.org/wiki/Special:Contributions/$oldestpagecreator">contrib.</a>) el $oldestpagecreationdate.</li> <- Añadir Special:Diff/XXXX/prev cuando se genere el page_creation_rev_id
            <li>La página más reciente es <a href="https://$wikilang.wikipedia.org/wiki/$newestpagetitle">$newestpagetitle</a>, creada por <a href="https://$wikilang.wikipedia.org/wiki/User:$newestpagecreator">$newestpagecreator</a> (<a href="https://$wikilang.wikipedia.org/wiki/Special:Contributions/$newestpagecreator">contrib.</a>) el $newestpagecreationdate.</li>
        </ul>
        <li>Se han encontrado <b>$totalcurrentevents</b> eventos de actualidad repartidos en <b>$totalcurrenteventspages</b> páginas.</li>
        <ul>
            <li>El evento de actualidad más antiguo sucedió en <a href="https://$wikilang.wikipedia.org/wiki/$oldestcurrenteventtitle">$oldestcurrenteventtitle</a>, fue insertado por <a href="https://$wikilang.wikipedia.org/wiki/User:$oldestcurrenteventuser">$oldestcurrenteventuser</a> (<a href="https://$wikilang.wikipedia.org/wiki/Special:Contributions/$oldestcurrenteventuser">contrib.</a>) el <a href="https://$wikilang.wikipedia.org/wiki/Special:Diff/$oldestcurrenteventrevid/prev">$oldestcurrenteventdate</a>.</li>
            <li>El evento de actualidad más reciente sucedió en <a href="https://$wikilang.wikipedia.org/wiki/$newestcurrenteventtitle">$newestcurrenteventtitle</a>, fue insertado por <a href="https://$wikilang.wikipedia.org/wiki/User:$newestcurrenteventuser">$newestcurrenteventuser</a> (<a href="https://$wikilang.wikipedia.org/wiki/Special:Contributions/$newestcurrenteventuser">contrib.</a>) el <a href="https://$wikilang.wikipedia.org/wiki/Special:Diff/$newestcurrenteventrevid/prev">$newestcurrenteventdate</a>.</li>
        </ul>
    </ul>
    
    $stats_by_year
    
    
    <!--
    Tipos de eventos más frecuentes
    Páginas que han recibido más eventos
    Páginas más editadas o con más editores durante eventos
    Días con más eventos de actualidad, eventos que se esparcen por varios artículos ({{current related}})
    -->
    
</body>
</html>
""")
    html = html.substitute(d)
    
    f = open('index.html', 'w')
    f.write(html)
    f.close()
    
if __name__ == '__main__':
    main()
