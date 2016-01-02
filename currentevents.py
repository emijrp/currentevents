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

#Dependencies:
#mediawiki-utilities: pip install mediawiki-utilities (https://github.com/halfak/mediawiki-utilities)
#p7zip-full (if dumps are .7z): sudo apt-get install p7zip-full

#Run: python script.py dumpfilename
#Or use the bash script

import csv
import datetime
import re
import subprocess
import sys

from mw.xml_dump import Iterator

#calcular la duracion media de la plantilla, en total y por tema

def pagemoved(revtext, prevrevtext):
    if revtext != '' and revtext == prevrevtext:
        return True
    return False

def timediff(start, end):
    t = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ") - datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
    return t

def timediffinhours(start, end):
    t = timediff(start, end)
    t = t.days * 24 + round(t.seconds/3600, 1)
    return t

def main():
    #current events templates regexp
    currentevent_templates_r = {
        "cawiki": re.compile(r'(?im)(\{\{\s*(?:Actualitat|Fet[ _]actual|Fets[ _]recents)\s*(?:\|[^\{\}\n]*?\s*\}\}|\}\}))'), 
        "dewiki": re.compile(r'(?im)(\{\{\s*(?:Laufendes[ _]Ereignis|Laufende[ _]Veranstaltung|Aktuelles[ _]Ereignis)\s*(?:\|[^\{\}\n]*?\s*\}\}|\}\}))'), 
        "enwiki": re.compile(r'(?im)(\{\{\s*(?:Current|Current[ _]antics|Current[ _]?disaster|Current[ _]election|Current[ _]?events?|Current[ _]news|Current[ _]paragraph|Current[ _]?person|Current[ _-]?related|Currentsect|Current[ _-]?section|Current[ _]spaceflight|Current[ _]?sport|Current[ _]sport-related|Current[ _]sports[ _]transaction|Current[ _]tornado[ _]outbreak|Current[ _]tropical[ _]cyclone|Current[ _]war|Currentwarfare|Flux|Live|Developing|Developingstory|Ongoing[ _]election|Ongoing[ _]event|Recent[ _]?death|Recent[ _]death[ _]presumed|Recent[ _]?event|Recent[ _]news|Recent[ _]related|Related[ _]current)\s*(?:\|[^\{\}\n]*?\s*\}\}|\}\}))'),
        "eswiki": re.compile(r'(?im)(\{\{\s*(?:Actual|Actualidad|Actualidad[ _]deporte|Current|EA|Evento[ _]actual|Launching|Muerte[ _]reciente|Sencillo[ _]actual|Single[ _]actual|Telenovela[ _]en[ _]emisión|Teleserie[ _]en[ _]emisión)\s*(?:\|[^\{\}\n]*?\s*\}\}|\}\}))'), 
        }
    #current events categories regexp
    currentevent_categories_r = {
        "cawiki": re.compile(r'(?im)\[\[\s*(?:Categoria|Category)\s*:\s*Articles[ _]d\'actualitat\s*[\|\]]'),
        "dewiki": re.compile(r'(?im)\[\[\s*(?:Kategorie|Category)\s*:\s*Wikipedia:Laufendes[ _]Ereignis\s*[\|\]]'),
        "enwiki": re.compile(r'(?im)\[\[\s*Category\s*:\s*Current[ _]events\s*[\|\]]'),
        "eswiki": re.compile(r'(?im)\[\[\s*(?:Categoría|Category)\s*:\s*Actualidad\s*[\|\]]'),
        }
    #namespaces to analyse
    wanted_namespaces = {
        "cawiki": [0], #main
        "dewiki": [0], #main
        "enwiki": [0], #main
        "eswiki": [0, 104], #main, anexo
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
        'tag_time_since_creation_(hours)', 
        'tag_duration_(hours)', 
        'tag_edits', 
        'tag_distinct_editors', 
        #'maintenance_templates', #templates for maintenance during current event
        'diff_len', 
        'diff_links', 
        'diff_extlinks', 
        'diff_refs', 
        'diff_templates', 
        'diff_images', 
        'page_moves', 
        #ideas: diff_sections
        ]
    #maintenance templates
    maintenance_templates_r = {
        "eswiki": re.compile(r'(?im)(\{\{\s*(?:Actualizar|Ampliación[ _]propuesta|Archivo|Artículo[ _]indirecto/esbozo|Artículo[ _]infraesbozo|Autotrad|Aviso[ _]infraesbozo|Bulo|Cita[ _]requerida|Complejo|Contextualizar|Copyedit|Copyvio|Curiosidades|Desactualizado|Desambiguación|Destruir|Discusión[ _]sosegada|Discutido|En[ _]desarrollo|En[ _]uso|Evento[ _]actual|Evento[ _]futuro|Excesivamente[ _]detallado|Ficticio|Formato[ _]de[ _]cita|FP|Fuentes[ _]no[ _]fiables|Fuente[ _]primaria|Fusionando|Fusionar|Fusionar[ _]desde|Fusionar[ _]en|Infraesbozo|Irrelevante|Largo|Mal[ _]traducido|Mejorar[ _]redacción|No[ _]es[ _]un[ _]foro|No[ _]neutralidad|Página[ _]bloqueada|Plagio|Plagio[ _]externo|Polémico|Posible[ _]copyvio|Posible[ _]fusionar|Problemas[ _]artículo|Promocional|Publicidad|PVfan|Reducido|Referencias|Referencias[ _]adicionales|Renombrar|Revisar[ _]traducción|Separado[ _]de|Separar|Sin[ _]?relevancia|SRA|Traducción|Traducido[ _]de|Transferir[ _]a|Wikificar)\s*(?:\|[^\{\}\n]*?\s*\}\}|\}\}))'),
    }
    #regexps for counts
    links_r = re.compile(r'(?im)(\[\[[^\[\]\r\n]+\]\])') # [[..|?..]]
    extlinks_r = re.compile(r'(?im)(://)') # ://
    refs_r = re.compile(r'(?im)< */ *ref *>') # </ref>
    templates_r = re.compile(r'(?im)((?:^|[^\{\}])\{\{[^\{\}])') # {{
    images_r = re.compile(r'(?im)\[\[\s*(File|Image|Fitxer|Imatge|Datei|Bild|Archivo|Imagen)\s*:')
    
    #get parameters
    dumpfilename = sys.argv[1]
    chunkid = sys.argv[2]
    #input can be compressed or plain xml
    if dumpfilename.endswith('.7z'):
        #7za or 7zr are valid
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
    dumpdate = datetime.datetime.strptime('%s 23:59:59' % (dumpfilename.split('/')[-1].split('-')[1]), '%Y%m%d %H:%M:%S')
    pagecount = 0
    
    #blank CSV currentevents
    filename = 'currentevents-%s-%s.csv.%s' % (dumplang, dumpdate.strftime('%Y%m%d'), chunkid)
    f = open(filename, 'w', encoding='utf-8')
    output = '{0}\n'.format('|'.join(fields))
    f.write(output)
    f.close()
    #blank CSV pages
    filename = 'pages-%s-%s.csv.%s' % (dumplang, dumpdate.strftime('%Y%m%d'), chunkid)
    g = open(filename, 'w', encoding='utf-8')
    output = 'page_id|page_namespace|page_title|page_creation_rev_id|page_creation_date|page_creator|page_is_redirect\n'
    g.write(output)
    g.close()
    
    #analyse dump
    for page in pages:
        if int(page.namespace) not in wanted_namespaces[dumplang]: #skip unwanted namespaces
            continue
        msg = 'Analysing: {0}'.format(page.title)
        print(msg.encode('utf-8'))
        
        pagecount += 1
        if pagecount % 100 == 0:
            msg = 'Analysed {0} pages'.format(pagecount)
            print(msg.encode('utf-8'))
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
        temp = {} # to detect wrongly removed templates
        prevrevtext = ''
        for rev in page:
            if revcount == 0:
                if rev.contributor:
                    page_creator = rev.contributor.user_text and rev.contributor.user_text or ''
                    page_creator_type = rev.contributor.id and rev.contributor.id != 0 and 'registered' or 'ip'
                else:
                    page_creator = ''
                    page_creator_type = 'unknown'
                pagecreationdate = rev.timestamp
                filename = 'pages-%s-%s.csv.%s' % (dumplang, dumpdate.strftime('%Y%m%d'), chunkid)
                g = csv.writer(open(filename, 'a', encoding='utf-8'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                g.writerow([page.id, page.namespace, page.title, rev.id, pagecreationdate.long_format(), page_creator, page_is_redirect])
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
                    #check page moves
                    if pagemoved(revtext, prevrevtext):
                        currentevents[-1]['page_moves'] += 1
                else:
                    #tagged as current event just now
                    if temp:
                        if timediffinhours(temp['rt_rev_timestamp'].long_format(), rev.timestamp.long_format()) <= 24 * 2:
                            #if it was current event less than X days before, then the template was wrongly removed
                            currentevents[-1] = temp.copy()
                            currentevents[-1]['tag_edits'] += 1
                            currentevents[-1]['tag_distinct_editors'].add(rev_user_text)
                            temp = {}
                            tagged = currentevents[-1]['it_rev_timestamp']
                            continue
                    
                    tagged = rev.timestamp
                    tag_time_since_creation = timediffinhours(pagecreationdate.long_format(), rev.timestamp.long_format())
                    print(page.title.encode('utf-8'), tag_time_since_creation)
                    
                    tag_string = 'unknown'
                    if re.search(currentevent_templates_r[dumplang], revtext):
                        #unify a bit the tag, to ease comparison later
                        tag_string = re.findall(currentevent_templates_r[dumplang], revtext)[0].lower().strip()
                        tag_string = re.sub(r'_', r' ', tag_string)
                        tag_string = re.sub(r'\{\{\s+', r'{{', tag_string)
                        tag_string = re.sub(r'\s+\}\}', r'}}', tag_string)
                        tag_string = re.sub(r'\s*\|\s*', r'|', tag_string)
                        tag_string = re.sub(r'\n', r'', tag_string)
                        tag_string = re.sub(r'\|\|+', r'|', tag_string)
                        tag_string = re.sub(r'(?i)\|\s*date\s*\=\s*[A-Za-z0-9 ]+', r'', tag_string) #remove |date=May 2014 in English WP
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
                        'page_creation_date': pagecreationdate, 
                        'it_rev_id': str(rev.id),
                        'it_rev_timestamp': rev.timestamp, 
                        'it_rev_username': rev.contributor.user_text, 
                        'it_rev_comment': revcomment and revcomment or "", 
                        'rt_rev_id': "",
                        'rt_rev_timestamp': "", 
                        'rt_rev_username': "", 
                        'rt_rev_comment': "", 
                        'tag_type': tag_type,
                        'tag_string': tag_string, 
                        'tag_time_since_creation_(hours)': str(tag_time_since_creation), 
                        'tag_duration_(hours)': "", 
                        'tag_edits': 1, #counter to increment
                        'tag_distinct_editors': set([rev_user_text]), #set of unique editors
                        #prevrevtext to catch any change right when is marked as current event
                        'diff_len': len(prevrevtext), 
                        'diff_links': len(re.findall(links_r, prevrevtext)), 
                        'diff_extlinks': len(re.findall(extlinks_r, prevrevtext)), 
                        'diff_refs': len(re.findall(refs_r, prevrevtext)), 
                        'diff_templates': len(re.findall(templates_r, prevrevtext)), 
                        'diff_images': len(re.findall(images_r, prevrevtext)), 
                        'page_moves': 0, 
                    }
                    currentevents.append(currentevent)
            else:
                if tagged:
                    #tag has been removed just now
                    
                    temp = currentevents[-1].copy() #saving temporaly to check if it is added again shortly
                    temp['rt_rev_timestamp'] = rev.timestamp
                    
                    currentevents[-1]['page_creation_date'] = currentevents[-1]['page_creation_date'].long_format()
                    currentevents[-1]['it_rev_timestamp'] = currentevents[-1]['it_rev_timestamp'].long_format()
                    currentevents[-1]['rt_rev_id'] = str(rev.id)
                    currentevents[-1]['rt_rev_timestamp'] = rev.timestamp.long_format()
                    currentevents[-1]['rt_rev_username'] = rev.contributor.user_text
                    currentevents[-1]['rt_rev_comment'] = revcomment and revcomment or ""
                    currentevents[-1]['tag_duration_(hours)'] = timediffinhours(tagged.long_format(), rev.timestamp.long_format())
                    currentevents[-1]['tag_edits'] += 1
                    currentevents[-1]['tag_distinct_editors'].add(rev_user_text)
                    currentevents[-1]['tag_distinct_editors'] = len(currentevents[-1]['tag_distinct_editors'])
                    currentevents[-1]['diff_len'] = len(revtext) - currentevents[-1]['diff_len']
                    #revtext because it was current event until this very edit
                    currentevents[-1]['diff_links'] = len(re.findall(links_r, revtext)) - currentevents[-1]['diff_links']
                    currentevents[-1]['diff_extlinks'] = len(re.findall(extlinks_r, revtext)) - currentevents[-1]['diff_extlinks']
                    currentevents[-1]['diff_refs'] = len(re.findall(refs_r, revtext)) - currentevents[-1]['diff_refs']
                    currentevents[-1]['diff_templates'] = len(re.findall(templates_r, revtext)) - currentevents[-1]['diff_templates']
                    currentevents[-1]['diff_images'] = len(re.findall(images_r, revtext)) - currentevents[-1]['diff_images']
                    currentevents[-1]['page_moves'] += 1
                    tagged = False
                else:
                    if temp:
                        #keep temp updated
                        temp['tag_edits'] += 1
                        temp['tag_distinct_editors'].add(rev_user_text)
                        #check page moves
                        if pagemoved(revtext, prevrevtext):
                            temp['page_moves'] += 1
            
            prevrevtext = revtext #needed for diff stats
        
        if tagged:
            #tagged still as of dumpdate
            currentevents[-1]['page_creation_date'] = currentevents[-1]['page_creation_date'].long_format()
            currentevents[-1]['it_rev_timestamp'] = currentevents[-1]['it_rev_timestamp'].long_format()
            currentevents[-1]['tag_duration_(hours)'] = timediffinhours(tagged.long_format(), dumpdate.strftime("%Y-%m-%dT%H:%M:%SZ"))
            currentevents[-1]['tag_edits'] += 1
            currentevents[-1]['tag_distinct_editors'].add(rev_user_text)
            currentevents[-1]['tag_distinct_editors'] = len(currentevents[-1]['tag_distinct_editors'])
            #use revtext and not prevrevtext because it is still current event
            currentevents[-1]['diff_len'] = len(revtext) - currentevents[-1]['diff_len']
            currentevents[-1]['diff_links'] = len(re.findall(links_r, revtext)) - currentevents[-1]['diff_links']
            currentevents[-1]['diff_extlinks'] = len(re.findall(extlinks_r, revtext)) - currentevents[-1]['diff_extlinks']
            currentevents[-1]['diff_refs'] = len(re.findall(refs_r, revtext)) - currentevents[-1]['diff_refs']
            currentevents[-1]['diff_templates'] = len(re.findall(templates_r, revtext)) - currentevents[-1]['diff_templates']
            currentevents[-1]['diff_images'] = len(re.findall(images_r, revtext)) - currentevents[-1]['diff_images']
            #print page.title.encode('utf-8'), currentevents[-1]
            tagged = False
    
        filename = 'currentevents-%s-%s.csv.%s' % (dumplang, dumpdate.strftime('%Y%m%d'), chunkid)
        f = csv.writer(open(filename, 'a', encoding='utf-8'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for i in currentevents:
            row = [i[field] for field in fields]
            f.writerow(row)
    
    print('Finished correctly')

if __name__ == '__main__':
    main()
