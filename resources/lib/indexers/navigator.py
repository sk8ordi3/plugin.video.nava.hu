# -*- coding: utf-8 -*-

'''
    NAVA Addon
    Copyright (C) 2023 heg, vargalex

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os, sys, re, xbmc, xbmcgui, xbmcplugin, xbmcaddon, locale, base64
from bs4 import BeautifulSoup
import requests
import urllib.parse
import resolveurl as urlresolver
from resources.lib.modules.utils import py2_decode, py2_encode
from datetime import datetime

sysaddon = sys.argv[0]
syshandle = int(sys.argv[1])
addonFanart = xbmcaddon.Addon().getAddonInfo('fanart')

KODI_VERSION_MAJOR = int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])

version = xbmcaddon.Addon().getAddonInfo('version')

addon_id = xbmcaddon.Addon().getAddonInfo('id')
addon = xbmcaddon.Addon(addon_id)
user_picked_option = addon.getSetting('searchSort')

search_sort_mapping = {"0":{"label":"Relevancia","value":""},"1":{"label":"Adásnap szerint csökkenő","value":"score desc, broadcast_date desc"},"2":{"label":"Adásnap szerint növekvő","value":"score desc, broadcast_date asc"},"3":{"label":"Cím (A-Z)","value":"sort_title asc"},"4":{"label":"Cím (Z-A)","value":"sort_title desc"},"5":{"label":"Dátum szerint csökkenő","value":"broadcast_date desc"},"6":{"label":"Dátum szerint növekvő","value":"broadcast_date asc"}}

selected_option = search_sort_mapping.get(user_picked_option, {})
search_sort_value = selected_option.get('value', '')
selected_label = selected_option.get('label', '')

if user_picked_option == int(user_picked_option):
    sort_final_result = ""
else:
    sort_final_result = f'"searchSort":"{search_sort_value}"'

hits_per_page = int(addon.getSetting('hitsPerPage'))
show_subtitle = addon.getSetting('showSubtitle')

kodi_version = xbmc.getInfoLabel('System.BuildVersion')
base_log_info = f'NAVA | v{version} | Kodi: {kodi_version[:5]}'

xbmc.log(f'{base_log_info}', xbmc.LOGINFO)

base_url = 'https://nava.hu'

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def normalize_url(url_x):
    if re.match(r'^//', url_x):
        return 'http:' + url_x
    else:
        return url_x

if sys.version_info[0] == 3:
    from xbmcvfs import translatePath
    from urllib.parse import urlparse, quote_plus, urlencode, unquote
else:
    from xbmc import translatePath
    from urlparse import urlparse
    from urllib import quote_plus

class navigator:
    def __init__(self):
        try:
            locale.setlocale(locale.LC_ALL, "hu_HU.UTF-8")
        except:
            try:
                locale.setlocale(locale.LC_ALL, "")
            except:
                pass
        self.base_path = py2_decode(translatePath(xbmcaddon.Addon().getAddonInfo('profile')))

    def root(self):
        self.addDirectoryItem("CSATORNA SZERINT", f"csat_items", '', 'DefaultFolder.png')
        self.addDirectoryItem("MŰFAJ SZERINT", f"mufaj_items", '', 'DefaultFolder.png')
        self.addDirectoryItem("KERESÉS", f"search", '', 'DefaultFolder.png')
        self.addDirectoryItem("KERESÉS (ID)", f"search_id", '', 'DefaultFolder.png')
        self.endDirectory()

    def getCsatItems(self, url, search_channel_value, search_channel_key):

        nava_channels_csat = {'searchChannel':{'RTL':'104','TV2':'103','Duna TV':'105','M1':'101','M2':'102','M3 Anno':'142','M4 Sport':'144','M5 Kultúra':'146','Duna World':'117','Dankó Rádió':'150','Bartók Rádió':'118','Petőfi Rádió':'122','Kossuth Rádió':'120','Echo TV':'148','ATV':'124','HírTV':'126','Mecenatúra Mozi':'mec','SZFE vizsgafilmek':'szfe','100 magyar film':'mnfa','MTV híradók':'mtv_hiradok','Mediawave':'mw','Mindentudás Egyeteme':'me','Euronews':'149','Néprajzi Múzeum':'nm','Szentendrei Teátrum':'szt','Semmelweis egészségpercek':'bokay','Erdély Kincsei':'erdelyk','Tudta-e? Jeles napok':'tudtae','NEK':'nek','Tudta-e? Népdalkincstár':'nepdalkincstar','Öveges professzor: Legkedvesebb kísérleteim':'oveges','Spektrum':'134','Spektrum Home':'135','Discovery Channel':'183','Comedy Central':'194'}}

        for search_channel_key, search_channel_value in nava_channels_csat['searchChannel'].items():
            data_x = {
                'mode': 'complex',
                'data': '{' + sort_final_result + (', ' if sort_final_result else '') + f'"searchChannel": "{search_channel_value}", "titlesButton": 1}}',
                'hitsPerPage': hits_per_page,
                'action': '',
            }
            
            encoded_data = urlencode(data_x)
            search_url = f"extr_csat_items&url={quote_plus(f'{base_url}/wp-content/plugins/hms-nava/interface/solrInterface.php?{encoded_data}')}&search_channel_value={search_channel_value}&search_channel_key={search_channel_key}"
            
            self.addDirectoryItem(search_channel_key, search_url, '', 'DefaultFolder.png')

        self.endDirectory()

    def extrCsatItems(self, url, doc_id, guide_description, ext_title, 
        firstFrame_image, duration, nava_genre, subtitle, 
        native_language, agelimit, vid_or_sound, main_description, 
        search_channel_value, search_channel_key):

        import requests
        
        response = requests.post(url, headers=headers, verify=False)
        
        data = response.json()
        print(f'\n{data}\n')
        docs = data['response']['docs']
        for doc in docs:
            doc_id = doc.get('id')
            collection = doc.get('collection')
            is_radio_technical = doc.get('isRadio_technical')
            if is_radio_technical:
                vid_or_sound = 'Hang'
            else:
                vid_or_sound = 'Videó'
            
            doc_title = doc.get('doc_title')
            sort_title = doc.get('sort_title')
            
            firstFrame_image = doc.get('secondFrame_image', [''])[0] or doc.get('firstFrame_image', [''])[0]
            firstFrame_image = normalize_url(firstFrame_image)
            
            nava_genre = doc.get('nava_genre', [''])[0]
            
            main_title = doc.get('main_title', [''])[0].replace('\n', '').replace('\r', '').replace('\t', '')
            
            guide_description = doc.get('guide_description', [''])[0].replace('\n', '').replace('\r', '').replace('\t', '')
            main_description = doc.get('main_description', [''])[0].replace('\n', '').replace('\r', '').replace('\t', '')
            
            native_language = doc.get('native_language', [''])[0]
            
            agelimit = doc.get('agelimit')
            if agelimit:
                pass
            else:
                agelimit = ''
            
            subtitle = doc.get('subtitle', [''])[0]
            if subtitle:
                subtitle = re.findall(r'\((.*.srt)', str(subtitle))[0].strip()
                subtitle = f'https://metadata.nava.hu/subtitle/{subtitle}'
            
            
            if guide_description == '':
                guide_description = main_description
            if main_description == '':
                main_description = guide_description
            
            real_begin_date = doc.get('realBegin_date')
            real_end_date = doc.get('realEnd_date')
            backup_duration = doc.get('duration')
            
            if (real_begin_date and real_end_date):
                to_normal_begin = datetime.strptime(real_begin_date, '%Y-%m-%dT%H:%M:%SZ')
                normal_begin_formatted = to_normal_begin.strftime('%Y-%m-%d %H:%M:%S')
            
                real_begin_date_object = datetime.strptime(real_begin_date, '%Y-%m-%dT%H:%M:%SZ')
                real_end_date_object = datetime.strptime(real_end_date, '%Y-%m-%dT%H:%M:%SZ')
            
                duration = int((real_end_date_object - real_begin_date_object).total_seconds())
            else:
                if backup_duration:
                    hours, minutes, seconds = map(int, backup_duration.split(':'))
                    duration = hours * 3600 + minutes * 60 + seconds
                else:
                    duration = 0
            
            if (real_begin_date and real_end_date):
                ext_title = f'{normal_begin_formatted} - {doc_title} #ID: {doc_id}'
            else:
                ext_title = f'{doc_title} #ID: {doc_id}'
            
            if main_description != guide_description:
                print(main_description)

            self.addDirectoryItem(f'[B]{ext_title}[/B]', f'get_mpd&doc_id={doc_id}&guide_description={guide_description}&ext_title={ext_title}&firstFrame_image={firstFrame_image}&duration={duration}&nava_genre={nava_genre}&subtitle={subtitle}&native_language={native_language}&agelimit={agelimit}&vid_or_sound={vid_or_sound}&main_description={main_description}', firstFrame_image, 'DefaultMovies.png', isFolder=True, meta={'title': ext_title, 'plot': f'[COLOR green]Típus:[/COLOR] {vid_or_sound}\n[COLOR lightblue]Kategória:[/COLOR] {nava_genre}\n[COLOR lightyellow]Nyelv:[/COLOR] {native_language}\n[COLOR orange]Leirás:[/COLOR] {main_description}', 'duration': f'{duration}'})
        
        try:
            resp_page_url = f'{response.url}'
            if re.search('pageFrom', resp_page_url):
                next_page_part_1 = re.findall(r'(.*pageFrom=)', str(resp_page_url))[0].strip()
                get_page_from_num = int(re.findall(r'&pageFrom=(\d+)&', str(resp_page_url))[0].strip())
                page_from_num_add_25 = get_page_from_num + 25
                next_page_url = f'{next_page_part_1}{page_from_num_add_25}&hitsPerPage={hits_per_page}&action='
            else:
                next_page_part_1 = re.findall(r'(.*)&hitsPerPage='+str(hits_per_page)+'&action=', str(resp_page_url))[0].strip()
                next_page_url = f'{next_page_part_1}&pageFrom=25&hitsPerPage={hits_per_page}&action='
            
            self.addDirectoryItem('[I]Következő oldal[/I]', f'extr_csat_items&url={quote_plus(next_page_url)}&search_channel_value={search_channel_value}&search_channel_key={search_channel_key}', '', 'DefaultFolder.png')
        except TypeError:
            xbmc.log(f'{base_log_info}| extrCsatItems | next_page_url | csak egy oldal található', xbmc.LOGINFO)
        
        
        self.endDirectory('series')

    def getMufajItems(self, url, search_channel_value, search_channel_key):

        nava_channels_mufaj = {'searchChannel':{"agrárműsor":"agrárműsor","aktuális esemény közvetítése":"aktuális esemény közvetítése","animáció":"animáció","beszélgetés, interjú, vita":"beszélgetés, interjú, vita","bulvár":"bulvár","csatornareklám":"csatornareklám","déli harangszó":"déli harangszó","dokumentum":"dokumentum","egyéb":"egyéb","esszé, jegyzet":"esszé, jegyzet","esélyegyenlőségi műsor":"esélyegyenlőségi műsor","film":"film","gazdasági műsor":"gazdasági műsor","gyermek- és ifjúsági műsor":"gyermek- és ifjúsági műsor","hangjáték":"hangjáték","határontúli műsor":"határontúli műsor","háttér- és közéleti műsor":"háttér- és közéleti műsor","heti hírösszefoglaló":"heti hírösszefoglaló","himnusz":"himnusz","hírműsor":"hírműsor","időjárás-jelentés":"időjárás-jelentés","információs magazin":"információs magazin","ismeretterjesztő # oktató műsor":"ismeretterjesztő / oktató műsor","kabaré":"kabaré","közérdekű közlemény":"közérdekű közlemény","kulturális # művészeti műsor":"kulturális / művészeti műsor","mese":"mese","műsorzárás":"műsorzárás","nemzetiségi # kisebbségi műsor":"nemzetiségi / kisebbségi műsor","parlamenti közvetítés":"parlamenti közvetítés","politikai hirdetés":"politikai hirdetés","portré":"portré","program # kulturális ajánló":"program / kulturális ajánló","regionális műsor":"regionális műsor","reklám":"reklám","riport":"riport","show-műsor # játék":"show-műsor / játék","sporthírek":"sporthírek","sportközvetítés":"sportközvetítés","sportmagazin":"sportmagazin","spot":"spot","szabadidő # életmód":"szabadidő / életmód","szappanopera":"szappanopera","szerencsejáték-sorsolás":"szerencsejáték-sorsolás","színház":"színház","szolgáltató műsor":"szolgáltató műsor","szórakoztató műsor (esztrád, varieté)":"szórakoztató műsor (esztrád, varieté)","talkshow":"talkshow","tánc":"tánc","társadalmi célú hirdetés":"társadalmi célú hirdetés","telefonos vetélkedő":"telefonos vetélkedő","természetfilm":"természetfilm","tévéjáték # tévéfilm":"tévéjáték / tévéfilm","tv-sorozat":"tv-sorozat","útifilm":"útifilm","választási műsor":"választási műsor","vallási műsor":"vallási műsor","valóságshow":"valóságshow","vers":"vers","vetélkedő":"vetélkedő","werkfilm":"werkfilm","zene":"zene"}}

        for search_channel_key, search_channel_value in nava_channels_mufaj['searchChannel'].items():
            data_x = {
                'mode': 'complex',
                'data': '{' + sort_final_result + (', ' if sort_final_result else '') + f'"searchGenre": "{search_channel_value}", "titlesButton": 1}}',
                'hitsPerPage': hits_per_page,
                'action': '',
            }
            
            encoded_data = urlencode(data_x)
            search_url = f"extr_mufaj_items&url={quote_plus(f'{base_url}/wp-content/plugins/hms-nava/interface/solrInterface.php?{encoded_data}')}&search_channel_value={search_channel_value}&search_channel_key={search_channel_key}"
            
            self.addDirectoryItem(search_channel_key, search_url, '', 'DefaultFolder.png')
        
        self.endDirectory()

    def extrMufajItems(self, url, doc_id, guide_description, ext_title, 
        firstFrame_image, duration, nava_genre, subtitle, 
        native_language, agelimit, vid_or_sound, main_description, 
        search_channel_value, search_channel_key):

        import requests
        
        response = requests.post(url, headers=headers, verify=False)
        
        data = response.json()
        print(f'\n{data}\n')
        docs = data['response']['docs']
        for doc in docs:
            doc_id = doc.get('id')
            collection = doc.get('collection')
            is_radio_technical = doc.get('isRadio_technical')
            if is_radio_technical:
                vid_or_sound = 'Hang'
            else:
                vid_or_sound = 'Videó'
            
            doc_title = doc.get('doc_title')
            sort_title = doc.get('sort_title')
            
            firstFrame_image = doc.get('secondFrame_image', [''])[0] or doc.get('firstFrame_image', [''])[0]
            firstFrame_image = normalize_url(firstFrame_image)
            
            nava_genre = doc.get('nava_genre', [''])[0]
            
            main_title = doc.get('main_title', [''])[0].replace('\n', '').replace('\r', '').replace('\t', '')
            
            guide_description = doc.get('guide_description', [''])[0].replace('\n', '').replace('\r', '').replace('\t', '')
            main_description = doc.get('main_description', [''])[0].replace('\n', '').replace('\r', '').replace('\t', '')
            
            native_language = doc.get('native_language', [''])[0]
            
            agelimit = doc.get('agelimit')
            if agelimit:
                pass
            else:
                agelimit = ''
            
            subtitle = doc.get('subtitle', [''])[0]
            if subtitle:
                subtitle = re.findall(r'\((.*.srt)', str(subtitle))[0].strip()
                subtitle = f'https://metadata.nava.hu/subtitle/{subtitle}'
            
            
            if guide_description == '':
                guide_description = main_description
            if main_description == '':
                main_description = guide_description
            
            real_begin_date = doc.get('realBegin_date')
            real_end_date = doc.get('realEnd_date')
            backup_duration = doc.get('duration')
            
            if (real_begin_date and real_end_date):
                to_normal_begin = datetime.strptime(real_begin_date, '%Y-%m-%dT%H:%M:%SZ')
                normal_begin_formatted = to_normal_begin.strftime('%Y-%m-%d %H:%M:%S')
            
                real_begin_date_object = datetime.strptime(real_begin_date, '%Y-%m-%dT%H:%M:%SZ')
                real_end_date_object = datetime.strptime(real_end_date, '%Y-%m-%dT%H:%M:%SZ')
            
                duration = int((real_end_date_object - real_begin_date_object).total_seconds())
            else:
                if backup_duration:
                    hours, minutes, seconds = map(int, backup_duration.split(':'))
                    duration = hours * 3600 + minutes * 60 + seconds
                else:
                    duration = 0
            
            if (real_begin_date and real_end_date):
                ext_title = f'{normal_begin_formatted} - {doc_title} #ID: {doc_id}'
            else:
                ext_title = f'{doc_title} #ID: {doc_id}'
            
            if main_description != guide_description:
                print(main_description)

            
            self.addDirectoryItem(f'[B]{ext_title}[/B]', f'get_mpd&doc_id={doc_id}&guide_description={guide_description}&ext_title={ext_title}&firstFrame_image={firstFrame_image}&duration={duration}&nava_genre={nava_genre}&subtitle={subtitle}&native_language={native_language}&agelimit={agelimit}&vid_or_sound={vid_or_sound}&main_description={main_description}', firstFrame_image, 'DefaultMovies.png', isFolder=True, meta={'title': ext_title, 'plot': f'[COLOR green]Típus:[/COLOR] {vid_or_sound}\n[COLOR lightblue]Kategória:[/COLOR] {nava_genre}\n[COLOR lightyellow]Nyelv:[/COLOR] {native_language}\n[COLOR orange]Leirás:[/COLOR] {main_description}', 'duration': f'{duration}'})
        
        try:
            resp_page_url = f'{response.url}'
            if re.search('pageFrom', resp_page_url):
                next_page_part_1 = re.findall(r'(.*pageFrom=)', str(resp_page_url))[0].strip()
                get_page_from_num = int(re.findall(r'&pageFrom=(\d+)&', str(resp_page_url))[0].strip())
                page_from_num_add_25 = get_page_from_num + 25
                next_page_url = f'{next_page_part_1}{page_from_num_add_25}&hitsPerPage={hits_per_page}&action='
            else:
                next_page_part_1 = re.findall(r'(.*)&hitsPerPage='+str(hits_per_page)+'&action=', str(resp_page_url))[0].strip()
                next_page_url = f'{next_page_part_1}&pageFrom=25&hitsPerPage={hits_per_page}&action='
            
            self.addDirectoryItem('[I]Következő oldal[/I]', f'extr_mufaj_items&url={quote_plus(next_page_url)}&search_channel_value={search_channel_value}&search_channel_key={search_channel_key}', '', 'DefaultFolder.png')
        except TypeError:
            xbmc.log(f'{base_log_info}| extrMufajItems | next_page_url | csak egy oldal található', xbmc.LOGINFO)

        self.endDirectory('series')

    def extrGetItems(self, url, doc_id, guide_description, ext_title, 
        firstFrame_image, duration, nava_genre, subtitle, 
        native_language, agelimit, vid_or_sound, main_description, 
        search_channel_value, search_channel_key):

        decoded_url = unquote(url)

        import requests
        
        response = requests.post(decoded_url, headers=headers, verify=False)
        
        data = response.json()
        print(f'\n{data}\n')
        docs = data['response']['docs']
        for doc in docs:
            doc_id = doc.get('id')
            collection = doc.get('collection')
            is_radio_technical = doc.get('isRadio_technical')
            if is_radio_technical:
                vid_or_sound = 'Hang'
            else:
                vid_or_sound = 'Videó'
            
            doc_title = doc.get('doc_title')
            sort_title = doc.get('sort_title')
            
            firstFrame_image = doc.get('secondFrame_image', [''])[0] or doc.get('firstFrame_image', [''])[0]
            firstFrame_image = normalize_url(firstFrame_image)
            
            nava_genre = doc.get('nava_genre', [''])[0]
            
            main_title = doc.get('main_title', [''])[0].replace('\n', '').replace('\r', '').replace('\t', '')
            
            guide_description = doc.get('guide_description', [''])[0].replace('\n', '').replace('\r', '').replace('\t', '')
            main_description = doc.get('main_description', [''])[0].replace('\n', '').replace('\r', '').replace('\t', '')
            
            native_language = doc.get('native_language', [''])[0]
            
            agelimit = doc.get('agelimit')
            if agelimit:
                pass
            else:
                agelimit = ''
            
            subtitle = doc.get('subtitle', [''])[0]
            if subtitle:
                subtitle = re.findall(r'\((.*.srt)', str(subtitle))[0].strip()
                subtitle = f'https://metadata.nava.hu/subtitle/{subtitle}'
            
            
            if guide_description == '':
                guide_description = main_description
            if main_description == '':
                main_description = guide_description
            
            real_begin_date = doc.get('realBegin_date')
            real_end_date = doc.get('realEnd_date')
            backup_duration = doc.get('duration')
            
            if (real_begin_date and real_end_date):
                to_normal_begin = datetime.strptime(real_begin_date, '%Y-%m-%dT%H:%M:%SZ')
                normal_begin_formatted = to_normal_begin.strftime('%Y-%m-%d %H:%M:%S')
            
                real_begin_date_object = datetime.strptime(real_begin_date, '%Y-%m-%dT%H:%M:%SZ')
                real_end_date_object = datetime.strptime(real_end_date, '%Y-%m-%dT%H:%M:%SZ')
            
                duration = int((real_end_date_object - real_begin_date_object).total_seconds())
            else:
                if backup_duration:
                    hours, minutes, seconds = map(int, backup_duration.split(':'))
                    duration = hours * 3600 + minutes * 60 + seconds
                else:
                    duration = 0
            
            if (real_begin_date and real_end_date):
                ext_title = f'{normal_begin_formatted} - {doc_title} #ID: {doc_id}'
            else:
                ext_title = f'{doc_title} #ID: {doc_id}'
            
            if main_description != guide_description:
                print(main_description)

            self.addDirectoryItem(f'[B]{ext_title}[/B]', f'get_mpd&doc_id={doc_id}&guide_description={guide_description}&ext_title={ext_title}&firstFrame_image={firstFrame_image}&duration={duration}&nava_genre={nava_genre}&subtitle={subtitle}&native_language={native_language}&agelimit={agelimit}&vid_or_sound={vid_or_sound}&main_description={main_description}', firstFrame_image, 'DefaultMovies.png', isFolder=True, meta={'title': ext_title, 'plot': f'[COLOR green]Típus:[/COLOR] {vid_or_sound}\n[COLOR lightblue]Kategória:[/COLOR] {nava_genre}\n[COLOR lightyellow]Nyelv:[/COLOR] {native_language}\n[COLOR orange]Leirás:[/COLOR] {main_description}', 'duration': f'{duration}'})
        
        try:
            resp_page_url = f'{response.url}'
            if re.search('pageFrom', resp_page_url):
                next_page_part_1 = re.findall(r'(.*pageFrom=)', str(resp_page_url))[0].strip()
                get_page_from_num = int(re.findall(r'&pageFrom=(\d+)&', str(resp_page_url))[0].strip())
                page_from_num_add_25 = get_page_from_num + 25
                next_page_url = f'{next_page_part_1}{page_from_num_add_25}&hitsPerPage={hits_per_page}&action='
            else:
                next_page_part_1 = re.findall(r'(.*)&hitsPerPage='+str(hits_per_page)+'&action=', str(resp_page_url))[0].strip()
                next_page_url = f'{next_page_part_1}&pageFrom=25&hitsPerPage={hits_per_page}&action='
            
            self.addDirectoryItem('[I]Következő oldal[/I]', f'extr_get_items&url={quote_plus(next_page_url)}&search_channel_value={search_channel_value}&search_channel_key={search_channel_key}', '', 'DefaultFolder.png')
        except TypeError:
            xbmc.log(f'{base_log_info}| extrGetItems | next_page_url | csak egy oldal található', xbmc.LOGINFO)
        
        
        self.endDirectory('series')

    def getMPD(self, doc_id, guide_description, ext_title, 
        firstFrame_image, duration, nava_genre, subtitle, 
        native_language, agelimit, vid_or_sound, main_description):

        import requests
        import re
        
        resp_00 = requests.get(f'{base_url}/id/{doc_id}/', headers=headers, verify=False).text
        
        try:
            custom_data = re.findall(r',\"widevine\":{\"customData\":\"(.*)\",\"certificateUri\"', str(resp_00))[0].strip()
        except IndexError:
            notification = xbmcgui.Dialog()
            notification.notification("NAVA", "Nincsen se videó se hang", time=5000)

        base_mpd = f'https://strlb.nava.hu/lbs/navahu_bdrm/_definst_/amlst:{doc_id}'
        
        import requests
        
        params = {
            'sessid': '',
            'omq': 'true',
            'np': '',
        }
        
        resp_01 = requests.head(base_mpd, params=params, headers=headers, allow_redirects=True, verify=False)
        mpd_url_part1 = resp_01.url
        
        import requests
        
        resp_02 = requests.get(mpd_url_part1, headers=headers, verify=False).text
        
        try:
            mpd_sample = re.findall(r'<Location>(.*)</Location>', str(resp_02))[0].strip()
        except IndexError:
            import requests
            import re
            
            data = {
                'prefix': '2',
                'vid': f'{doc_id}',
            }
            
            resp_x = requests.post('https://nava.hu/wp-content/plugins/hms-nava/interface/getVideoStatus.php', data=data, verify=False).text
            
            if re.search('ON_TAPE', resp_x):
                notification = xbmcgui.Dialog()
                notification.notification("NAVA", f"{resp_x} A kért műsor jelenleg szalagon található", time=5000)
        
        mpd_mod = re.findall(r"https?:.+\.mpd(?!\?)", str(mpd_sample))[0].strip()
        
        xbmc.log(f'{base_log_info}| getMpdLic | vid_or_sound | {vid_or_sound}', xbmc.LOGINFO)
        xbmc.log(f'{base_log_info}| getMpdLic | duration | {duration}', xbmc.LOGINFO)
        xbmc.log(f'{base_log_info}| getMpdLic | subtitle | {subtitle}', xbmc.LOGINFO)
        
        if vid_or_sound == 'Videó':
            mpd_mod = re.sub("_w[0-9]+", "_w999999999", mpd_mod)
            mpd_mod = re.sub("_ps[0-9]+", "_ps0000100", mpd_mod)
            mpd_mod = re.sub("_pd[0-9]+", "_pd60000000", mpd_mod)
        elif vid_or_sound == 'Hang':
            from datetime import timedelta
            
            try:
                h, m, s = duration.split(':')
                delta = timedelta(hours=int(h), minutes=int(m), seconds=int(s))
                inms = int(delta.total_seconds()*1000)
                inmsplus = inms+120000
                
                mpd_mod = re.sub("_w[0-9]+", "_w9999999999", mpd_mod)
                mpd_mod = re.sub("_pd[0-9]+", '_pd'+str(inmsplus)+'', mpd_mod)
            except ValueError:
                duration_seconds = int(duration)
                
                hours = duration_seconds // 3600
                minutes = (duration_seconds % 3600) // 60
                seconds = duration_seconds % 60
                
                duration = '{:02d}:{:02d}:{:02d}'.format(hours, minutes, seconds)
                
                h, m, s = duration.split(':')
                delta = timedelta(hours=int(h), minutes=int(m), seconds=int(s))
                inms = int(delta.total_seconds()*1000)
                inmsplus = inms+120000
                
                mpd_mod = re.sub("_w[0-9]+", "_w9999999999", mpd_mod)
                mpd_mod = re.sub("_pd[0-9]+", '_pd'+str(inmsplus)+'', mpd_mod)
        
        play_item = xbmcgui.ListItem(path=mpd_mod)
        
        play_item.setInfo('video', {'title': ext_title, 'plot': f'[COLOR green]Típus:[/COLOR] {vid_or_sound}\n[COLOR lightblue]Kategória:[/COLOR] {nava_genre}\n[COLOR lightyellow]Nyelv:[/COLOR] {native_language}\n[COLOR orange]Leirás:[/COLOR] {main_description}', 'duration': f'{duration}'})
        play_item.setArt({'poster': firstFrame_image})        
        
        if subtitle is not None and show_subtitle == 'true':
            play_item.setSubtitles([subtitle])
        
        play_item.setProperty('inputstream', 'inputstream.adaptive')
        
        if KODI_VERSION_MAJOR == 19:
            play_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            
        elif KODI_VERSION_MAJOR == 20:
            play_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        
        play_item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
        play_item.setProperty('inputstream.adaptive.stream_headers', 'verifypeer=false')
        play_item.setProperty('inputstream.adaptive.manifest_headers', 'verifypeer=false')
        
        license_headers = {
            'customdata': custom_data,
        }
        
        from urllib.parse import urlencode
        
        license_config = {
            'license_server_url': 'https://wv-keyos.licensekeyserver.com/',
            'headers': urlencode(license_headers),
            'post_data': 'R{SSM}',
            'response_data':'',
        }
        play_item.setProperty('inputstream.adaptive.license_key', '|'.join(license_config.values()))
        
        xbmc.Player().play(mpd_mod, play_item)

    def doSearch(self, url):
        search_text = self.getSearchText()
        if search_text != '':
            if not os.path.exists(self.base_path):
                os.mkdir(self.base_path)

            data = {
                'mode': 'complex',
                'data': '{' + sort_final_result + (', ' if sort_final_result else '') + f'"searchText":"{search_text}","subjectWordButton":1,"personsButton":1,"titlesButton":1,"descriptionButton":1}}',
                'hitsPerPage': hits_per_page,
                'action': '',
            }
            
            encoded_data = urlencode(data)
            url_x = f"{base_url}/wp-content/plugins/hms-nava/interface/solrInterface.php?{encoded_data}"
            url = quote_plus(url_x)
            
            self.extrGetItems(url, None, None, None, None, None, None, None, None, None, None, None, None, None)

    def doSearch_2(self, url):
        search_text = self.getSearchText_2()
        if search_text != '':
            if not os.path.exists(self.base_path):
                os.mkdir(self.base_path)

            data = {
                'mode': 'complex',
                'data': f'{{"searchText":"ID: {search_text}","subjectWordButton":1}}',
                'hitsPerPage': hits_per_page,
                'action': '',
            }
            
            encoded_data = urlencode(data)
            url_x = f"{base_url}/wp-content/plugins/hms-nava/interface/solrInterface.php?{encoded_data}"
            url = quote_plus(url_x)
            
            self.extrGetItems(url, None, None, None, None, None, None, None, None, None, None, None, None, None)            

    def getSearchText(self):
        search_text = ''
        keyb = xbmc.Keyboard('', u'Add meg a M\xfbsor c\xedm\xe9t')
        keyb.doModal()
        if keyb.isConfirmed():
            search_text = keyb.getText()
        return search_text

    def getSearchText_2(self):
        search_text = ''
        keyb = xbmc.Keyboard('', u'Csak az ID-t add meg pl. mnfa-84')
        keyb.doModal()
        if keyb.isConfirmed():
            search_text = keyb.getText()
        return search_text        

    def addDirectoryItem(self, name, query, thumb, icon, context=None, queue=False, isAction=True, isFolder=True, Fanart=None, meta=None, banner=None):
        url = f'{sysaddon}?action={query}' if isAction else query
        if thumb == '':
            thumb = icon
        cm = []
        if queue:
            cm.append((queueMenu, f'RunPlugin({sysaddon}?action=queueItem)'))
        if not context is None:
            cm.append((context[0].encode('utf-8'), f'RunPlugin({sysaddon}?action={context[1]})'))
        item = xbmcgui.ListItem(label=name)
        item.addContextMenuItems(cm)
        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': thumb, 'banner': banner})
        if Fanart is None:
            Fanart = addonFanart
        item.setProperty('Fanart_Image', Fanart)
        if not isFolder:
            item.setProperty('IsPlayable', 'true')
        if not meta is None:
            item.setInfo(type='Video', infoLabels=meta)
        xbmcplugin.addDirectoryItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)

    def endDirectory(self, type='addons'):
        xbmcplugin.setContent(syshandle, type)
        xbmcplugin.endOfDirectory(syshandle, cacheToDisc=True)