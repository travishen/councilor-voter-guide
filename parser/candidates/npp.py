#! /usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append('../')
import re
import os
import json
import requests
import subprocess

import db_settings
import common


def councilor_terms(candidate):
    '''
    Parse working recoed before the election_year of this candidate into a json to store in individual candidate, so we could display councilor's working records easier at candidate page(no need of a lot of reference).
    '''

    c.execute('''
        SELECT id as term_id, councilor_id, election_year, param, to_char(EXTRACT(YEAR FROM term_start), '9999') as term_start_year, substring(term_end->>'date' from '(\d+)-') as term_end_year
        FROM councilors_councilorsdetail
        WHERE councilor_id = %(councilor_uid)s AND election_year <= %(election_year)s
        ORDER BY election_year DESC
    ''', candidate)
    key = [desc[0] for desc in c.description]
    terms = []
    r = c.fetchall()
    for row in r:
        terms.append(dict(zip(key, row)))
    return terms

def upsertCandidates(candidate):
    candidate['former_names'] = candidate.get('former_names', [])
    variants = common.make_variants_set(candidate['name'])
    candidate['identifiers'] = list((variants | set(candidate['former_names']) | {candidate['name'], re.sub(u'[\w‧]', '', candidate['name']), re.sub(u'\W', '', candidate['name']).lower(), }) - {''})
    complement = {'birth': None, 'gender': '', 'party': '', 'number': None, 'contact_details': None, 'district': '', 'education': None, 'experience': None, 'remark': None, 'image': '', 'links': None, 'platform': '', 'data': None}
    complement.update(candidate)
    c.execute('''
        INSERT INTO candidates_candidates(uid, name, birth, identifiers)
        VALUES (%(candidate_uid)s, %(name)s, %(birth)s, %(identifiers)s)
        ON CONFLICT (uid)
        DO UPDATE
        SET name = %(name)s, birth = %(birth)s, identifiers = %(identifiers)s
    ''', complement)
    c.execute('''
        INSERT INTO candidates_terms(uid, candidate_id, elected_councilor_id, councilor_terms, election_year, number, name, gender, party, constituency, county, district, contact_details, education, experience, remark, image, links, platform, type)
        VALUES (%(candidate_term_uid)s, %(candidate_uid)s, %(councilor_term_id)s, %(councilor_terms)s, %(election_year)s, %(number)s, %(name)s, %(gender)s, %(party)s, %(constituency)s, %(county)s, %(district)s, %(contact_details)s, %(education)s, %(experience)s, %(remark)s, %(image)s, %(links)s, %(platform)s, %(type)s)
        ON CONFLICT (election_year, candidate_id)
        DO UPDATE
        SET elected_councilor_id = %(councilor_term_id)s, councilor_terms = %(councilor_terms)s, number = %(number)s, name = %(name)s, gender = %(gender)s, party = %(party)s, constituency = %(constituency)s, county = %(county)s, district = %(district)s, contact_details = %(contact_details)s, education = %(education)s, experience = %(experience)s, remark = %(remark)s, image = %(image)s, links = %(links)s
    ''', complement)

conn = db_settings.con()
c = conn.cursor()
election_year = '2018'
party = u'時代力量'
path = '../../data/avatar/councilors/%s/%s' % (election_year, party)

constituencies = json.load(open('../../voter_guide/static/json/dest/constituencies_%s.json' % election_year))
#candidates = json.load(open('npp.json'))
candidates = requests.get('https://npp.vote/api/v1/candidates').json()
for row in candidates['data']:
    county = requests.get('https://npp.vote/api/v1/cities/%s' % row['relationships']['city']['data']['id']).json()['data']['attributes']['name']
    row = row['attributes']
    if not row['name'] or row['name'] == u'即將推出':
        continue
    candidate = {}
    candidate['type'] = 'councilors'
    candidate['county'] = county.replace(u'台', u'臺')
    print candidate['county'], row['region'], row['name']
    for co, di, no in [(u'宜蘭縣', u'宜蘭市', 1), (u'宜蘭縣', u'頭城鎮', 2), (u'宜蘭縣', u'羅東鎮', 6), (u'臺東縣', u'台東、蘭嶼', 1), (u'臺東縣', u'東河、成功、長濱', 3), (u'屏東縣', u'萬丹、東港、新園', 4), (u'屏東縣', u'崁頂、林邊、南州、佳冬', 5), (u'澎湖縣', u'馬公', 1), (u'雲林縣', u'斗六、林內、莿桐', 1), (u'雲林縣', u'西螺、二崙、崙背', 4), (u'彰化縣', u'彰化、花壇、芬園', 1), (u'苗栗縣', u'竹南、造橋、後龍', 4), (u'苗栗縣', u'頭份、三灣、南庄', 5), (u'新竹縣', u'竹北', 1), (u'新北市', u'新莊、泰山、五股、林口', 2), (u'新北市', u'新店、深坑、石碇、坪林、烏來', 8), (u'新北市', u'汐止、金山、萬里', 10), (u'花蓮縣', u'玉里、瑞穗、富里、卓溪之平地原住民', 7), (u'花蓮縣', u'吉安、壽豐、豐濱、鳳林、萬榮、光復', 3), (u'花蓮縣', u'鳳林、壽豐、光復、豐濱、萬榮之平地原住民', 6), ]:
        if co == county and di == row['region']:
            candidate['constituency'] = no
    if not candidate.get('constituency'):
        for item in constituencies:
            if item['county'] == candidate['county'] and set(item['district'].split(u'、')) == set(row['region'].split(u'、')):
                candidate['constituency'] = item['constituency']
    print candidate['constituency']
    candidate['name'] = common.normalize_person_name(row['name'])
    candidate['party'] = party
    candidate['election_year'] = election_year
    candidate['number'] = row['vote_number'] if row['vote_number'] else None
    candidate['platform'] = row['info']
    candidate['education'] = row['school']
    candidate['experience'] = row['experience']
    contact_mappings = {
        'phone': u'電話',
        'fax': u'傳真',
        'address': u'通訊處',
        'email': u'電子信箱'
    }
    candidate['contact_details'] = []
    for key, value in row['contact'].items():
        candidate['contact_details'].append({
            'label': contact_mappings[key],
            'type': value,
            'value': value
        })
    candidate['links'] = []
    for key, value in row['social_media'].items():
        candidate['links'].append({'url': value, 'note': key})
    f_name = '%s_%d_%s.%s' % (candidate['county'], candidate['constituency'], candidate['name'], row['avatar'].split('.')[-1].split('?')[0])
    f = '%s/%s' % (path, f_name)
    if not os.path.isfile(f):
        cmd = 'wget --no-check-certificate "%s" -O %s' % (row['avatar'], f)
        subprocess.call(cmd, shell=True)
    candidate['image'] = u'%s/%s/%s/%s/%s' % (common.storage_domain(), candidate['type'], election_year, party, f_name)
    candidate['candidate_uid'], created = common.get_or_create_candidate_uid(c, candidate)
    candidate['candidate_term_uid'] = '%s-%s' % (candidate['candidate_uid'], election_year)
    candidate['councilor_uid'], created = common.get_or_create_councilor_uid(c, candidate)
    candidate['councilor_term_id'] = common.getDetailIdFromUid(c, candidate['councilor_uid'], election_year, candidate['county'])

    candidate['councilor_terms'] = councilor_terms(candidate) if created else None
    upsertCandidates(candidate)
conn.commit()