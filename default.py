# -*- coding: utf-8 -*-

'''
    NAVA Add-on
    Copyright (C) 2020 heg, vargalex

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
import sys
from resources.lib.indexers import navigator

if sys.version_info[0] == 3:
    from urllib.parse import parse_qsl
else:
    from urlparse import parse_qsl

params = dict(parse_qsl(sys.argv[2].replace('?', '')))

action = params.get('action')
url = params.get('url')

doc_id = params.get('doc_id')
guide_description = params.get('guide_description')
ext_title = params.get('ext_title')
firstFrame_image = params.get('firstFrame_image')
duration = params.get('duration')
nava_genre = params.get('nava_genre')
subtitle = params.get('subtitle')
native_language = params.get('native_language')
agelimit = params.get('agelimit')
vid_or_sound = params.get('vid_or_sound')
main_description = params.get('main_description')
search_channel_value = params.get('search_channel_value')
search_channel_key = params.get('search_channel_key')

if action is None:
    navigator.navigator().root()

elif action == 'movie_categories':
    navigator.navigator().getMovieCategories()

elif action == 'csat_items':
    navigator.navigator().getCsatItems(url, search_channel_value, search_channel_key)

elif action == 'extr_csat_items':
    navigator.navigator().extrCsatItems(url, doc_id, guide_description, ext_title, firstFrame_image, duration, nava_genre, subtitle, native_language, agelimit, vid_or_sound, main_description, search_channel_value, search_channel_key)

elif action == 'mufaj_items':
    navigator.navigator().getMufajItems(url, search_channel_value, search_channel_key)

elif action == 'extr_mufaj_items':
    navigator.navigator().extrMufajItems(url, doc_id, guide_description, ext_title, firstFrame_image, duration, nava_genre, subtitle, native_language, agelimit, vid_or_sound, main_description, search_channel_value, search_channel_key)

elif action == 'extr_get_items':
    navigator.navigator().extrGetItems(url, doc_id, guide_description, ext_title, firstFrame_image, duration, nava_genre, subtitle, native_language, agelimit, vid_or_sound, main_description, search_channel_value, search_channel_key)

elif action == 'get_mpd':
    navigator.navigator().getMPD(doc_id, guide_description, ext_title, firstFrame_image, duration, nava_genre, subtitle, native_language, agelimit, vid_or_sound, main_description)

elif action == 'search':
    navigator.navigator().doSearch(url)

elif action == 'search_id':
    navigator.navigator().doSearch_2(url)    