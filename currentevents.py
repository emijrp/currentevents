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
#añadir un campo is_redirect al csv de newpages para diferenciar entre articulos y redirecciones

def timediff(start, end):
    t = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ") - datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
    return t

def main():
    limitdays = 7 #template must be inserted before X days since page creation
    #current events templates regexp
    currentevent_templates_r = {
        #"enwiki": re.compile(r'(?im)(\{\{\s*()\s*[\|\}]([^\}\n]*?)\}\}?)'),
        "eswiki": re.compile(r'(?im)(\{\{\s*(Actual|Actualidad|Actualidad[ _]deporte|Current|EA|Evento[ _]actual|Launching|Muerte[ _]reciente|Sencillo[ _]actual|Single[ _]actual|Telenovela[ _]en[ _]emisión|Teleserie[ _]en[ _]emisión)\s*[\|\}]([^\}\n]*?)\}\}?)'),
        }
    #current events categories regexp
    currentevent_categories_r = {
        "enwiki": re.compile(r'(?im)\[\[\s*Category\s*:\s*Current[ _]events\s*[\|\]]'),
        "eswiki": re.compile(r'(?im)\[\[\s*Categor(y|ía)\s*:\s*Actualidad\s*[\|\]]'),
        }
    #namespaces to analyse
    wanted_namespaces = {
        "eswiki": [0], #main
        }
    #fields to generate
    fields = [
        'page_id', 
        'page_namespace', 
        'page_title', 
        'page_creator', 
        'page_creator_type', #ip, registered, unknown
        'page_creation_date', 
        'it_rev_id', #it = inserted tag
        'it_rev_timestamp', 
        'it_rev_username', 
        'it_rev_comment', 
        'rt_rev_id', #rt = removed tag
        'rt_rev_timestamp', 
        'rt_rev_username', 
        'rt_rev_comment', 
        'tag_type', #template, category, both
        'tag_string', 
        'tag_time_since_creation', 
        'tag_duration', 
        'tag_edits', 
        'tag_distinct_editors', 
        ]
    #get parameters
    dumpfilename = sys.argv[1]
    chunkid = sys.argv[2]
    #input can be compressed or plain xml
    if dumpfilename.endswith('.7z'):
        #7za or 7zr are valid
        fp = subprocess.Popen('7zr e -bd -so %s 2>/dev/null' % dumpfilename, shell=True, stdout=subprocess.PIPE, bufsize=65535)
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
    
    #blank CSV
    f = open('currentevents-%s-%s.csv.%s' % (dumplang, dumpdate.strftime('%Y%m%d'), chunkid), 'w')
    f.write('%s\n' % ('|'.join(fields)))
    f.close()
    #blank newpages
    g = open('newpages-%s-%s.csv.%s' % (dumplang, dumpdate.strftime('%Y%m%d'), chunkid), 'w')
    g.write('page_id|page_namespace|page_title|page_creation_date|page_creator|page_is_redirect\n')
    g.close()
    
    #analyse dump
    for page in pages:
        if int(page.namespace) not in wanted_namespaces[dumplang]: #skip unwanted namespaces
            continue
        print('Analysing:', page.title.encode('utf-8'))
        
        pagecount += 1
        if pagecount % 100 == 0:
            print('Analysed',pagecount,'pages')
        #if pagecount > 2000:
        #    if dumpfilename.endswith('.7z'):
        #        fp.kill()
        #    break
        
        currentevents = []
        tagged = False
        revcount = 0
        page_creator = ''
        page_creator_type = ''
        pagecreationdate = ''
        page_is_redirect = page.redirect and 'True' or 'False'
        for rev in page:
            if revcount == 0:
                if rev.contributor:
                    page_creator = rev.contributor.user_text and rev.contributor.user_text or ''
                    page_creator_type = rev.contributor.id and rev.contributor.id != 0 and 'registered' or 'ip'
                else:
                    page_creator = ''
                    page_creator_type = 'unknown'
                pagecreationdate = rev.timestamp
                g = csv.writer(open('newpages-%s-%s.csv.%s' % (dumplang, dumpdate.strftime('%Y%m%d'), chunkid), 'a'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                g.writerow([page.id, page.namespace, page.title, pagecreationdate.long_format(), page_creator, page_is_redirect])
            revcount += 1
            #print (rev.id)
            rev_user_text = ''
            if rev.contributor:
                rev_user_text = rev.contributor.user_text and rev.contributor.user_text or ''
            revtext = rev.text and rev.text or ''
            revcomment = re.sub(r'\n', '', rev.comment and rev.comment or '')
            if re.search(currentevent_templates_r[dumplang], revtext) or re.search(currentevent_categories_r[dumplang], revtext):
                if tagged:
                    #still is current event
                    currentevents[-1]['tag_edits'] += 1
                    currentevents[-1]['tag_distinct_editors'].add(rev_user_text)
                else:
                    #tagged as current event just now
                    tagged = rev.timestamp
                    tag_time_since_creation = timediff(pagecreationdate.long_format(), rev.timestamp.long_format())
                    print(page.title.encode('utf-8'), tag_time_since_creation)
                    #if tag_time_since_creation.days >= limitdays: #skip if article was created >X days ago
                    #    break #we are in a date in history that is away >limitdays from page creation, so skip this page, no more to see here
                    
                    tag_string = 'unknown'
                    if re.search(currentevent_templates_r[dumplang], revtext):
                        #unify a bit the tag, to ease comparison later
                        tag_string = re.findall(currentevent_templates_r[dumplang], revtext)[0][0].lower().strip()
                        tag_string = re.sub(r'_', r' ', tag_string)
                        tag_string = re.sub(r'\{\{\s+', r'{{', tag_string)
                        tag_string = re.sub(r'\s+\}\}', r'}}', tag_string)
                        tag_string = re.sub(r'\s*\|\s*', r'|', tag_string)
                    tag_type = ""
                    if re.search(currentevent_templates_r[dumplang], revtext):
                        tag_type = "template"
                        if re.search(currentevent_categories_r[dumplang], revtext):
                            tag_type = "both"
                    elif re.search(currentevent_categories_r[dumplang], revtext):
                        tag_type = "category"

                    currentevent = {
                        'page_id': str(page.id), 
                        'page_namespace': str(page.namespace), 
                        'page_title': page.title, 
                        'page_creator': page_creator, 
                        'page_creator_type': page_creator_type, 
                        'page_creation_date': pagecreationdate.long_format(), 
                        'it_rev_id': str(rev.id),
                        'it_rev_timestamp': rev.timestamp.long_format(), 
                        'it_rev_username': rev.contributor.user_text, 
                        'it_rev_comment': revcomment and revcomment or "", 
                        'rt_rev_id': "",
                        'rt_rev_timestamp': "", 
                        'rt_rev_username': "", 
                        'rt_rev_comment': "", 
                        'tag_type': tag_type,
                        'tag_string': tag_string, 
                        'tag_time_since_creation': str(tag_time_since_creation), 
                        'tag_duration': "", 
                        'tag_edits': 1, #counter to increment
                        'tag_distinct_editors': set([rev_user_text]), #set of unique editors
                    }
                    currentevents.append(currentevent)
            else:
                if tagged:
                    #tag has been removed just now
                    currentevents[-1]['rt_rev_id'] = str(rev.id)
                    currentevents[-1]['rt_rev_timestamp'] = rev.timestamp.long_format()
                    currentevents[-1]['rt_rev_username'] = rev.contributor.user_text
                    currentevents[-1]['rt_rev_comment'] = revcomment and revcomment or ""
                    currentevents[-1]['tag_duration'] = timediff(tagged.long_format(), rev.timestamp.long_format())
                    currentevents[-1]['tag_edits'] += 1
                    currentevents[-1]['tag_distinct_editors'].add(rev_user_text)
                    currentevents[-1]['tag_distinct_editors'] = len(currentevents[-1]['tag_distinct_editors'])
                    tagged = False

        if tagged:
            #tag still as of dumpdate
            currentevents[-1]['tag_duration'] = timediff(tagged.long_format(), dumpdate.strftime("%Y-%m-%dT%H:%M:%SZ"))
            currentevents[-1]['tag_edits'] += 1
            currentevents[-1]['tag_distinct_editors'].add(rev_user_text)
            currentevents[-1]['tag_distinct_editors'] = len(currentevents[-1]['tag_distinct_editors'])
            #print page.title.encode('utf-8'), currentevents[-1]
            tagged = False
    
        f = csv.writer(open('currentevents-%s-%s.csv.%s' % (dumplang, dumpdate.strftime('%Y%m%d'), chunkid), 'a'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for i in currentevents:
            row = [i[field] for field in fields]
            f.writerow(row)
    
    print('Finished correctly')

if __name__ == '__main__':
    main()
