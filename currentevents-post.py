# -*- coding: utf-8 -*-

# Copyright (C) 2014-2016 emijrp <emijrp@gmail.com>
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
import statistics
import string
import sys

currentevents = {}
pages = {}

def mergefiles(csvfiles):
    csvfiles.sort()
    if csvfiles:
        prefixfile = csvfiles[0].split('.1')[0]
        os.system('cp {0}.1 {0}'.format(prefixfile))
        for csvfile in csvfiles[1:]:
            os.system('tail -q -n +2 {0} >> {1}'.format(csvfile, prefixfile))

def loadCurrentEventsCSV(csvfile):
    global currentevents
    
    c = 0
    f = csv.reader(open(csvfile, 'r'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    d = {}
    for row in f:
        if c == 0:
            c += 1
            continue
        
        currentevents[int(row[6])] = {
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
            'tag_time_since_creation_(hours)': float(row[16]),
            'tag_duration_(hours)': float(row[17]),
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

def loadPagesCSV(csvfile):
    global pages
    
    c = 0
    f = csv.reader(open(csvfile, 'r'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    d = {}
    for row in f:
        if c == 0:
            c += 1
            continue
        
        pages[int(row[0])] = {
            'page_id': int(row[0]), 
            'page_namespace': int(row[1]), 
            'page_title': row[2], 
            'page_creation_date': row[3], 
            'page_creator': row[4], 
            'page_is_redirect': row[5] == 'True' and True or False, 
        }
        c += 1

def main():
    global currentevents
    global pages
    
    resultdirs = glob.glob("/data/project/currentevents/public_html/*wiki/20*")
    resultdirs.sort()
    for resultdir in resultdirs:
        dumpwiki, dumpdate = resultdir.split('/')[-2:]
        print('Postprocessing',dumpwiki,dumpdate)
        print('Reading CSV from',resultdir)
        
        #error logs
        errorlogs = glob.glob("%s/%s*.err" % (resultdir, dumpwiki))
        errorlogs.sort()
        timereal = 0
        for errorlog in errorlogs:
            f = open(errorlog, 'r')
            raw = f.read()
            f.close()
            m = re.findall(r'(?im)real\s*(\d+)m', raw) #real    570m46.569s
            if m:
                if int(m[0]) > timereal:
                    timereal = int(m[0])
        
        #currentevents csv
        currentevents = {}
        csvfiles = glob.glob("%s/currentevents-%s-%s.csv.*" % (resultdir, dumpwiki, dumpdate))
        csvfiles.sort()
        for csvfile in csvfiles:
            print('Loading',csvfile)
            loadCurrentEventsCSV(csvfile)
        print('Loaded',len(currentevents.items()),'current events')
        mergefiles(csvfiles)
        
        #pages csv
        pages = {}
        csvfiles = glob.glob("%s/pages-%s-%s.csv.*" % (resultdir, dumpwiki, dumpdate))
        csvfiles.sort()
        for csvfile in csvfiles:
            print('Loading',csvfile)
            loadPagesCSV(csvfile)
        print('Loaded',len(pages.items()),'pages')
        mergefiles(csvfiles)
        
        #dict for stats
        num2namespace = {
            'cawiki': {0:'Principal'}, 
            'dewiki': {0:'Principal'}, 
            'enwiki': {0:'Principal'}, 
            'eswiki': {0:'Principal', 104:'Anexo'}, 
        }
        namespaces = list(set([v['page_namespace'] for k, v in currentevents.items()]))
        namespaces.sort()
        d = {
            'csvlinks': '<li><a href="currentevents-{0}-{1}.csv">currentevents-{0}-{1}.csv</a></li>\n<li><a href="pages-{0}-{1}.csv">pages-{0}-{1}.csv</a></li>\n'.format(dumpwiki, dumpdate), 
            'timereal': round(timereal/60, 2), 
            'dumpdate': dumpdate, 
            
            'diffeditsmean': round(statistics.mean([v['tag_edits'] for k, v in currentevents.items()]), 1),
            'diffeditsmedian': round(statistics.median([v['tag_edits'] for k, v in currentevents.items()]), 1),
            'diffeditsmode': round(statistics.mode([v['tag_edits'] for k, v in currentevents.items()]), 1),
            
            'diffeditorsmean': round(statistics.mean([v['tag_distinct_editors'] for k, v in currentevents.items()]), 1),
            'diffeditorsmedian': round(statistics.median([v['tag_distinct_editors'] for k, v in currentevents.items()]), 1),
            'diffeditorsmode': round(statistics.mode([v['tag_distinct_editors'] for k, v in currentevents.items()]), 1),
            
            'difflenmean': round(statistics.mean([v['diff_len'] for k, v in currentevents.items()]), 1),
            'difflenmedian': round(statistics.median([v['diff_len'] for k, v in currentevents.items()]), 1),
            'difflenmode': round(statistics.mode([v['diff_len'] for k, v in currentevents.items()]), 1),
            
            'difflinksmean': round(statistics.mean([v['diff_links'] for k, v in currentevents.items()]), 1),
            'difflinksmedian': round(statistics.median([v['diff_links'] for k, v in currentevents.items()]), 1),
            'difflinksmode': round(statistics.mode([v['diff_links'] for k, v in currentevents.items()]), 1),
            
            'diffextlinksmean': round(statistics.mean([v['diff_extlinks'] for k, v in currentevents.items()]), 1),
            'diffextlinksmedian': round(statistics.median([v['diff_extlinks'] for k, v in currentevents.items()]), 1),
            'diffextlinksmode': round(statistics.mode([v['diff_extlinks'] for k, v in currentevents.items()]), 1),
            
            'diffrefsmean': round(statistics.mean([v['diff_refs'] for k, v in currentevents.items()]), 1),
            'diffrefsmedian': round(statistics.median([v['diff_refs'] for k, v in currentevents.items()]), 1),
            'diffrefsmode': round(statistics.mode([v['diff_refs'] for k, v in currentevents.items()]), 1),
            
            'difftemplatesmean': round(statistics.mean([v['diff_templates'] for k, v in currentevents.items()]), 1),
            'difftemplatesmedian': round(statistics.median([v['diff_templates'] for k, v in currentevents.items()]), 1),
            'difftemplatesmode': round(statistics.mode([v['diff_templates'] for k, v in currentevents.items()]), 1),
            
            'diffimagesmean': round(statistics.mean([v['diff_images'] for k, v in currentevents.items()]), 1),
            'diffimagesmedian': round(statistics.median([v['diff_images'] for k, v in currentevents.items()]), 1),
            'diffimagesmode': round(statistics.mode([v['diff_images'] for k, v in currentevents.items()]), 1),
            
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
            
            'tagtypetemplate': sum([v['tag_type'] == 'template' for k, v in currentevents.items()]),
            'tagtypecategory': sum([v['tag_type'] == 'category' for k, v in currentevents.items()]),
            'tagtypeboth': sum([v['tag_type'] == 'both' for k, v in currentevents.items()]),
            
            'tagdurationdaysmean': round(statistics.mean([round(v['tag_duration_(hours)']/24, 0) for k, v in currentevents.items()]), 1),
            'tagdurationdaysmedian': round(statistics.median([round(v['tag_duration_(hours)']/24, 0) for k, v in currentevents.items()]), 1),
            'tagdurationdaysmode': round(statistics.mode([round(v['tag_duration_(hours)']/24, 0) for k, v in currentevents.items()]), 1),
            
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
        max_tag_time_since_creation_hours = 24 # max hours
        stats_by_year = {}
        for k, v in currentevents.items():
            year = int(v['it_rev_timestamp'].split('-')[0])
            if not year in stats_by_year:
                stats_by_year[year] = {'currentevents': 0, 'currenteventpages': set([]), 'currenteventpagescreated': set([]), 'totalpagescreated': 0}
            
            stats_by_year[year]['currentevents'] += 1
            stats_by_year[year]['currenteventpages'].add(v['page_id'])
            if v['tag_time_since_creation_(hours)'] <= max_tag_time_since_creation_hours:
                stats_by_year[year]['currenteventpagescreated'].add(v['page_id'])
            
        for k, v in pages.items():
            if v['page_is_redirect']:
                continue
            year = int(v['page_creation_date'].split('-')[0])
            if year in stats_by_year:
                stats_by_year[year]['totalpagescreated'] += 1
        
        stats_by_year = [[k, v] for k, v in stats_by_year.items()]
        stats_by_year.sort()
        stats_by_year_table = '\n'.join(["<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td></tr>".format(k, v['currentevents'], len(v['currenteventpages']), len(v['currenteventpagescreated']), v['totalpagescreated']) for k, v in stats_by_year])
        stats_by_year_table += "<tr><td><b>Total</b></td>"
        stats_by_year_table += "<td><b>{0}</b></td>".format(sum([v['currentevents'] for k, v in stats_by_year]))
        stats_by_year_table += "<td><b>{0}</b></td>".format(sum([len(v['currenteventpages']) for k, v in stats_by_year]))
        stats_by_year_table += "<td><b>{0}</b></td>".format(sum([len(v['currenteventpagescreated']) for k, v in stats_by_year]))
        stats_by_year_table += "<td><b>{0}</b></td></tr>".format(sum([v['totalpagescreated'] for k, v in stats_by_year]))
        d['stats_by_year_table'] = "<table border=1 style='text-align: center;'>\n<th>Año</th><th>Eventos de actualidad</th><th>Páginas diferentes marcadas como actualidad</th><th>Páginas creadas por evento de actualidad</th><th>Páginas totales creadas</th>\n{0}\n</table>".format(stats_by_year_table)
        
        #stats by page
        stats_by_page = {}
        for k, v in currentevents.items():
            if v['page_id'] in stats_by_page:
                stats_by_page[v['page_id']]['currentevents'].append(k)
                stats_by_page[v['page_id']]['dates'].append('<a href="https://{0}.wikipedia.org/wiki/Special:Diff/{1}/prev">{2}</a>'.format(d['wikilang'], k, v['it_rev_timestamp'].split('T')[0]))
            else:
                stats_by_page[v['page_id']] = {
                    'currentevents': [k], 
                    'dates': ['<a href="https://{0}.wikipedia.org/wiki/Special:Diff/{1}/prev">{2}</a>'.format(d['wikilang'], k, v['it_rev_timestamp'].split('T')[0])]
                }
        most_freq_pages = [[len(v['currentevents']), k, v['dates']] for k, v in stats_by_page.items()]
        most_freq_pages.sort(reverse=True)
        stats_by_page_table = '\n'.join(['<tr><td><a href="https://{0}.wikipedia.org/wiki/{1}">{1}</a></td><td>{2}</td><td>{3}</td></tr>'.format(d['wikilang'], pages[rev_id]['page_title'], c, ', '.join(dates)) for c, rev_id, dates in most_freq_pages[:100]])
        d['stats_by_page_table'] = "<table border=1 style='text-align: center;'>\n<th>Página</th><th>Veces marcada como evento actual</th><th>Fechas en las que fue marcado</th>\n{0}\n</table>".format(stats_by_page_table)
        
        #stats by event
        stats_by_event = {'conflict': 0, 'death': 0, 'disaster': 0, 'election': 0, 'film': 0, 'health': 0, 'music': 0, 'spaceflight': 0, 'sports': 0, 'television': 0, 'videogames': 0, 'weather': 0, 'other': 0}
        other_events = {}
        for k, v in currentevents.items():
            if re.search(r'(conflict|conflicto|guerra|war)', v['tag_string']):
                stats_by_event['conflict'] += 1
            elif re.search(r'(dead|death|defunció|fallecimiento|mort|muerte)', v['tag_string']):
                stats_by_event['death'] += 1
            elif re.search(r'(desastre|disaster)', v['tag_string']):
                stats_by_event['disaster'] += 1
            elif re.search(r'(elecci[óo]n|elecciones|eleccions|election)', v['tag_string']):
                stats_by_event['election'] += 1
            elif re.search(r'(film|pel·l[ií]cula|pel[íi]cula)', v['tag_string']):
                stats_by_event['film'] += 1
            elif re.search(r'(health|salud|salut)', v['tag_string']):
                stats_by_event['health'] += 1
            elif re.search(r'(sencillo|single)', v['tag_string']):
                stats_by_event['music'] += 1
            elif re.search(r'(spaceflight|vol espacial|vuelo espacial)', v['tag_string']):
                stats_by_event['spaceflight'] += 1
            elif re.search(r'(deporte|b[àa]squet|baloncesto|f[úu]tbol|sport)', v['tag_string']):
                stats_by_event['sports'] += 1
            elif re.search(r'(televisi[óo]n|telenovela|serie de televisi[óo]n|serie de tv)', v['tag_string']):
                stats_by_event['television'] += 1
            elif re.search(r'(videogame|videojoc)', v['tag_string']):
                stats_by_event['videogames'] += 1
            elif re.search(r'(meteorolog[íi]a|weather)', v['tag_string']):
                stats_by_event['weather'] += 1
            else:
                stats_by_event['other'] += 1
                if v['tag_string'] in other_events:
                    other_events[v['tag_string']] += 1
                else:
                    other_events[v['tag_string']] = 1
            
        stats_by_event = [[v, k] for k, v in stats_by_event.items()]
        stats_by_event.sort(reverse=True)
        stats_by_event_table = '\n'.join(['<tr><td>{0}</td><td>{1}</td></tr>'.format(event, c) for c, event in stats_by_event])
        other_events = [[v, k] for k, v in other_events.items()]
        other_events.sort(reverse=True)
        other_events_table = ', '.join(['{0} ({1})'.format(event, c) for c, event in other_events[:100]])
        d['stats_by_event_table'] = "<table border=1 style='text-align: center;'>\n<th>Evento de actualidad</th><th>Páginas diferentes marcadas con este evento</th><th>Páginas creadas por este evento</th>\n{0}\n</table>\n\n<p>Los más frecuentes dentro de \"Other\": {1}, ...</p>".format(stats_by_event_table, other_events_table)
        
        html = string.Template("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html lang="en" dir="ltr" xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Current events ($wiki, $dumpdate)</title>
    <meta http-equiv="content-type" content="text/html;charset=utf-8" />
</head>
<body>
    <h1><a href="https://tools.wmflabs.org/currentevents">Current events</a> ($wiki, $dumpdate)</h1>
    
    <p>Este análisis de <b>eventos de actualidad</b> corresponde a <b><a href="https://$wikilang.wikipedia.org">$wiki</a></b> con la fecha <b>$dumpdate</b>.
    
    <p>Se ha generado en <b>$timereal</b> horas. Estos son los datos en bruto:</p>
    <ul>
        $csvlinks
    </ul>
    
    <h2>Resumen general</h2>
    
    <p>A continuación se ofrece un <b>resumen general</b>:</p>
    <ul>
        <li>Se han analizado páginas de <b>$totalnamespaces</b> espacios de nombres: $namespaces.</li>
        <li>Se han encontrado <b>$totalusefulpages</b> páginas de contenido y <b>$totalredirects</b> redirecciones. En total <b>$totalpages</b> páginas.</li>
        <ul>
            <li>El <b>$usefulpagespercent%</b> son páginas de contenido y el <b>$redirectspercent%</b> son redirecciones.</li>
            <li>La página más antigua es <a href="https://$wikilang.wikipedia.org/wiki/$oldestpagetitle">$oldestpagetitle</a>, creada por <a href="https://$wikilang.wikipedia.org/wiki/User:$oldestpagecreator">$oldestpagecreator</a> (<a href="https://$wikilang.wikipedia.org/wiki/Special:Contributions/$oldestpagecreator">contrib.</a>) el $oldestpagecreationdate.</li> <- Añadir Special:Diff/XXXX/prev cuando se genere el page_creation_rev_id
            <li>La página más reciente es <a href="https://$wikilang.wikipedia.org/wiki/$newestpagetitle">$newestpagetitle</a>, creada por <a href="https://$wikilang.wikipedia.org/wiki/User:$newestpagecreator">$newestpagecreator</a> (<a href="https://$wikilang.wikipedia.org/wiki/Special:Contributions/$newestpagecreator">contrib.</a>) el $newestpagecreationdate.</li>
        </ul>
        
        <li>Se han encontrado <b>$totalcurrentevents</b> eventos de actualidad repartidos en <b>$totalcurrenteventspages</b> páginas diferentes.</li>
        <ul>
            <li>Para marcarlo como evento de actualidad, <b>$tagtypetemplate</b> usaron solo plantilla, <b>$tagtypecategory</b> usaron solo categoría y <b>$tagtypeboth</b> usaron ambos métodos.</li>
            <li>La duración (en días) de la marca actualidad es: <b>$tagdurationdaysmean</b> (media), <b>$tagdurationdaysmedian</b> (mediana), <b>$tagdurationdaysmode</b> (moda)
            <li>El evento de actualidad más antiguo sucedió en <a href="https://$wikilang.wikipedia.org/wiki/$oldestcurrenteventtitle">$oldestcurrenteventtitle</a>, fue insertado por <a href="https://$wikilang.wikipedia.org/wiki/User:$oldestcurrenteventuser">$oldestcurrenteventuser</a> (<a href="https://$wikilang.wikipedia.org/wiki/Special:Contributions/$oldestcurrenteventuser">contrib.</a>) el <a href="https://$wikilang.wikipedia.org/wiki/Special:Diff/$oldestcurrenteventrevid/prev">$oldestcurrenteventdate</a>.</li>
            <li>El evento de actualidad más reciente sucedió en <a href="https://$wikilang.wikipedia.org/wiki/$newestcurrenteventtitle">$newestcurrenteventtitle</a>, fue insertado por <a href="https://$wikilang.wikipedia.org/wiki/User:$newestcurrenteventuser">$newestcurrenteventuser</a> (<a href="https://$wikilang.wikipedia.org/wiki/Special:Contributions/$newestcurrenteventuser">contrib.</a>) el <a href="https://$wikilang.wikipedia.org/wiki/Special:Diff/$newestcurrenteventrevid/prev">$newestcurrenteventdate</a>.</li>
        </ul>
        
        <li>En cuanto a los cambios que se producen en los artículos, hay un incremento en:</li>
        <ul>
            <li>Número de ediciones: <b>$diffeditsmean</b> (media), <b>$diffeditsmedian</b> (mediana), <b>$diffeditsmode</b> (moda)
            <li>Número de editores distintos: <b>$diffeditorsmean</b> (media), <b>$diffeditorsmedian</b> (mediana), <b>$diffeditorsmode</b> (moda)
            <li>Tamaño en bytes: <b>$difflenmean</b> (media), <b>$difflenmedian</b> (mediana), <b>$difflenmode</b> (moda)
            <li>Número de enlaces: <b>$difflinksmean</b> (media), <b>$difflinksmedian</b> (mediana), <b>$difflinksmode</b> (moda)
            <li>Número de enlaces externos: <b>$diffextlinksmean</b> (media), <b>$diffextlinksmedian</b> (mediana), <b>$diffextlinksmode</b> (moda)
            <li>Número de referencias: <b>$diffrefsmean</b> (media), <b>$diffrefsmedian</b> (mediana), <b>$diffrefsmode</b> (moda)
            <li>Número de plantillas: <b>$difftemplatesmean</b> (media), <b>$difftemplatesmedian</b> (mediana), <b>$difftemplatesmode</b> (moda)
            <li>Número de imágenes: <b>$diffimagesmean</b> (media), <b>$diffimagesmedian</b> (mediana), <b>$diffimagesmode</b> (moda)
        </ul>
    </ul>
    
    <h2>Por años</h2>
    
    $stats_by_year_table
    
    <h2>Por páginas</h2>
    
    $stats_by_page_table
    
    <h2>Por eventos</h2>
    
    $stats_by_event_table
    
    <!--
    Páginas más editadas o con más editores durante eventos
    Días con más eventos de actualidad, eventos que se esparcen por varios artículos ({{current related}})
    -->
    
</body>
</html>
""")
        html = html.substitute(d)
        outputpath = '%s/index.html' % (resultdir)
        print('Saving HTML in',outputpath,'\n')
        f = open(outputpath, 'w')
        f.write(html)
        f.close()
    
    resultsul = ''
    prevdumpwiki = ''
    for resultdir in resultdirs:
        dumpwiki, dumpdate = resultdir.split('/')[-2:]
        if prevdumpwiki != dumpwiki:
            if prevdumpwiki != '':
                resultsul += '\n    </ul>'
            resultsul += '\n    <li><b>%s</b></li>' % (dumpwiki)
            resultsul += '\n    <ul>\n        <li><a href="%s/%s/index.html">%s</a></li>' % (dumpwiki, dumpdate, dumpdate)
        else:
            resultsul += '\n        <li><a href="%s/%s/index.html">%s</a></li>' % (dumpwiki, dumpdate, dumpdate)
        prevdumpwiki = dumpwiki
    resultsul += '\n    </ul>'
    e = {
        'resultsul': resultsul,
    }
    html = string.Template("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html lang="en" dir="ltr" xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Current events</title>
    <meta http-equiv="content-type" content="text/html;charset=utf-8" />
</head>
<body>
    <h1><a href="https://tools.wmflabs.org/currentevents">Current events</a></h1>
    
    <p>Estos son los <b>análisis de eventos de actualidad</b> disponibles.</p>
    
    <ul>
        $resultsul
    </ul>
    
</body>
</html>""")
    html = html.substitute(e)
    outputpath = 'index.html'
    print('Saving HTML in',outputpath)
    f = open(outputpath, 'w')
    f.write(html)
    f.close()
    
if __name__ == '__main__':
    main()
