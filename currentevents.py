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

#Dependencies:
#mediawiki-utilities: pip install mediawiki-utilities (https://github.com/halfak/mediawiki-utilities)
#p7zip-full (if dumps are .7z): sudo apt-get install p7zip-full

#Run: python script.py dumpfilename

import csv
import datetime
import re
import subprocess
import sys

from mw.xml_dump import Iterator

#https://es.wikipedia.org/wiki/Plantilla:Evento_actual
#calcular la duracion media de la plantilla, en total y por tema
#cuando hay un vandalismo/blanqueo que quita la plantilla y revierten, hace como que quitan y vuelven a meter la plantilla (mejor saltar estas entradas/salidas? comparar el texto de la revid -1 y revid +1 para ver si son iguales)

def timediff(start, end):
    t = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ") - datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
    return t

def main():
    limitdays = 7 #template must be inserted before X days since page creation
    #current events templates for different wikis
    currentevents_r = {
        "eswiki": re.compile(r'(?im)(\{\{\s*(Actual|Actualidad|Actualidad[ _]deporte|Current|EA|Evento[ _]actual|Launching|Muerte[ _]reciente|Sencillo[ _]actual|Single[ _]actual|Telenovela[ _]en[ _]emisión|Teleserie[ _]en[ _]emisión)\s*[\|\}]([^\}]*?)\}\}?)'),
        }
    wanted_namespaces = {
        "eswiki": [0], #main
        }
    fields = [
        'page_title', 
        'page_creation_date', 
        'template_time_since_creation', 
        'it_rev_id', #it = inserted template
        'it_rev_timestamp', 
        'it_rev_username', 
        'it_rev_comment', 
        'event_type', 
        'rt_rev_id', #rt = removed template
        'rt_rev_timestamp', 
        'rt_rev_username', 
        'rt_rev_comment', 
        'template_duration', 
        ]
    dumpfilename = sys.argv[1]
    chunkid = sys.argv[2]
    if dumpfilename.endswith('.7z'):
        fp = subprocess.Popen('7za e -bd -so %s 2>/dev/null' % dumpfilename, shell=True, stdout=subprocess.PIPE, bufsize=65535)
        pages = Iterator.from_file(fp.stdout)
    elif dumpfilename.endswith('.bz2'):
        import bz2
        source = bz2.BZ2File(dumpfilename)
        pages = Iterator.from_file(source)
    else:
        source = open(dumpfilename)
        pages = Iterator.from_file(source)
    
    #get dump language and date
    dumplang = dumpfilename.split('/')[-1].split('-')[0]
    dumpdate = datetime.datetime.strptime(dumpfilename.split('/')[-1].split('-')[1], '%Y%m%d')
    pagecount = 0
    
    #start CSV
    f = open('currentevents-%s-%s.csv.%s' % (dumplang, dumpdate.strftime('%Y%m%d'), chunkid), 'w')
    f.write('%s\n' % ('|'.join(fields)))
    f.close()
    #blank newpages
    g = open('newpages-%s-%s.csv.%s' % (dumplang, dumpdate.strftime('%Y%m%d'), chunkid), 'w')
    g.write('page_title|page_creation_date\n')
    g.close()
    
    #analyse dump
    for page in pages:
        currentevents = []
        if page.namespace not in wanted_namespaces[dumplang]: #skip unwanted pages
            continue
        print ('Analysing:', page.title.encode('utf-8'))
        pagecount += 1
        if pagecount % 100 == 0:
            print('Analysed',pagecount,'pages')
        #if pagecount > 2000:
        #    fp.kill()
        #    break
        insertedtemplate = False
        revcount = 0
        pagecreationdate = ''
        for rev in page:
            if revcount == 0:
                pagecreationdate = rev.timestamp
                g = csv.writer(open('newpages-%s-%s.csv.%s' % (dumplang, dumpdate.strftime('%Y%m%d'), chunkid), 'a'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                g.writerow([page.title, pagecreationdate.long_format()])
            revcount += 1
            #print (rev.id)
            revtext = rev.text and rev.text or ''
            revcomment = re.sub(r'\n', '', rev.comment and rev.comment or '')
            if re.search(currentevents_r[dumplang], revtext):
                if insertedtemplate:
                    pass #template is still in page
                else:
                    #template has been inserted
                    #skip if article was created >X days ago
                    template_time_since_creation = timediff(pagecreationdate.long_format(), rev.timestamp.long_format())
                    print(page.title.encode('utf-8'), template_time_since_creation)
                    if template_time_since_creation.days >= limitdays:
                        break #we are in a date in history that is away >limitdays from page creation, so skip this page, no more to see here
                        
                    insertedtemplate = rev.timestamp
                    eventtype = True and re.findall(currentevents_r[dumplang], revtext)[0][2] or 'Unknown'
                    currentevent = {
                        'page_title': page.title, 
                        'page_creation_date': pagecreationdate.long_format(), 
                        'template_time_since_creation': str(template_time_since_creation), 
                        'event_type': eventtype, 
                        'template_duration': "", 
                        'it_rev_id': str(rev.id), #it = inserted template
                        'it_rev_timestamp': rev.timestamp.long_format(), 
                        'it_rev_username': rev.contributor.user_text, 
                        'it_rev_comment': True and revcomment or "", 
                        'rt_rev_id': "", #rt = removed template
                        'rt_rev_timestamp': "", 
                        'rt_rev_username': "", 
                        'rt_rev_comment': "", 
                    }
                    currentevents.append(currentevent)
            else:
                if insertedtemplate:
                    #template has been removed just now
                    currentevents[-1]['template_duration'] = timediff(insertedtemplate.long_format(), rev.timestamp.long_format())
                    currentevents[-1]['rt_rev_comment'] = revcomment and revcomment or ""
                    currentevents[-1]['rt_rev_username'] = rev.contributor.user_text
                    currentevents[-1]['rt_rev_timestamp'] = rev.timestamp.long_format()
                    currentevents[-1]['rt_rev_id'] = str(rev.id)
                    insertedtemplate = False

        if insertedtemplate:
            #template still as of dumpdate
            currentevents[-1]['template_duration'] = timediff(insertedtemplate.long_format(), dumpdate.strftime("%Y-%m-%dT%H:%M:%SZ"))
            #print page.title, currentevents[-1]
    
        f = csv.writer(open('currentevents-%s-%s.csv.%s' % (dumplang, dumpdate.strftime('%Y%m%d'), chunkid), 'a'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for i in currentevents:
            row = [i[field] for field in fields]
            f.writerow(row)

if __name__ == '__main__':
    main()
