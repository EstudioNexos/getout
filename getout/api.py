#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import ast
import requests

from bs4 import BeautifulSoup
from slugify import slugify
import codecs
import logging
from lookupy import Collection, Q

LOG_FILENAME = 'getout.log'
logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.INFO,
                    )

DNS_RECORD_TYPES = [
    'A',
    'AAAA',
    'SOA',
    'MX',
    'PTR',
    'SRV',
    'TXT',
    'NS',
    'CNAME',
    'SSHFP'
]
# Utilities
def clean_string(string):
    string = string.replace('\/','/')
    return string

def remove_shit(string):
    string = string.replace('\t','').replace('\n','')
    return string
    
def hydrate(text):
    #~ print(text)
    evaluated = ast.literal_eval(text)
    #~ evaluated2 = ast.literal_eval(evaluated)
    #~ print(evaluated2)
    HTML = evaluated[3]['ARGS']['HTML']
    
    HTML = "<html><body><table>%s</table></body></html>" % HTML.replace("\/","/")
    #~ print(HTML)
    return HTML
    
def endpoint(data):
    response = open(data)
    return response.read()
    
class CDMON(object):
    s = requests.Session()
    auth_url = 'https://admin.cdmon.com/es/acceso'
    index_url = 'https://admin.cdmon.com'
    domains_url_subfix = '/es/dns/listado-registros'
    domains_url_list = '/es/dns/listado-dominios'
    summary = None

    def __init__(self, *args, **kwargs):
        self.password = kwargs.get('password')
        self.user = kwargs.get('user')
        self.services_url = self.index_url + '/es/inicio'
        self.s.headers.update({'Accept-Encoding': 'identity, deflate, compress, gzip'})
        self.auth()
        self.get_hash()
    
    def get_soup(self, text):
        soup = BeautifulSoup(text, "lxml")
        return soup
        
    def get_hash(self):
        index_r = self.s.get(self.index_url)
        soup = self.get_soup(index_r.text)
        hashinput = soup.find_all("input", attrs={"name": "dades[hash]"})
        self.ourhash = hashinput[0].get('value')
    
    def auth(self, *args, **kwargs):
        auth_payload = {'action': 'iniciarSessio', 'dades[contrasenya]': self.password, 'dades[site]': 'admin', 'dades[usuario]': self.user}
        auth_r = self.s.post(self.auth_url, auth_payload)
        logging.debug('Logged in CDMON')
    
    def all(self, *args, **kwargs):
        self.get_summary()
        detailed = self.detail_list()
        return detailed

    def add_domain(self, name):
        callback = {
            'dades[hash]': self.ourhash,
            'dades[domini]': name,
            'action': 'nouDominiDns',
        }
        r = self.s.post(self.index_url + self.domains_url_list, data=callback)
        self.get_summary()
        domain_dict = list(self.summary.filter(name__exact=name))
        if len(domain_dict) > 0:
            return domain_dict[0]
        logging.info('Error adding domain %s' % name)

    def get(self, name):
        self.get_summary()
        find = list(self.summary.filter(name__exact=name))
        if len(find) > 0:
            domain = find[0]
            return self.get_details(domain)
        
    def get_summary(self, *args, **kwargs):
        if not self.summary:
            self.summary = self.parse_all()
        return self.summary
            
    def record_exists(self, records, record_type, host):
        check = list(records.filter(record_type__exact=record_type, host__exact=host))
        if len(check) == 0:
            logging.info("Does not exist %s,%s" % record_type, record_host)
            return False
        return check[0]

    def set_record(self, domain, record_type, host, destination=False, value=False, weight=False, priority='', redir_code=3):
        domain_name = domain['canonical_name']
        exists = self.record_exists(domain['records'], record_type, host)
        if exists == False:
            logging.info("Creating record for %s" % domain['name'])
            record_type = record_type.lower()
            callback = {
                'dades[hash]': self.ourhash,
                'dades[id]': domain_name,
                'dades[tipus]': record_type,
                'dades[host]': host,
                'action': 'crearRegistre',
            }
            if destination:
                callback['dades[desti]'] = destination
            if value:
                callback['dades[valor]'] = value
            if record_type == 'mx':
                callback['dades[prioritat]'] = priority
                callback['dades[redir]'] = 3
            if record_type == 'a':
                callback['dades[redir]'] = redir_code
            r_set_record = self.s.post(self.index_url + self.domains_url_subfix, data=callback)
            domain['records'] = self.get_records(domain)
        else:
            logging.info("Record exists %s" % exists)
        return domain

    def get_details(self, domain):
        logging.info("Getting details %s" % domain['slug'])
        name =  domain['name']
        if '\u00f1' in name:
            name = name.replace('\u00f1',u'ñ')
        mng_url = self.index_url + u'/es/dominios/principal'
        response = self.s.get(mng_url, params={'dades[dom]':name}, allow_redirects=True)
        soup = self.get_soup(response.text)
        items = soup.find_all('li', role="listitem")
        domain['records'] =  Collection([])
        if len(items) > 0:
            domain['status'] = False
            domain['locked'] = True
            domain['notifications'] = True
            domain['private_whois'] = True
            domain['automatic_renovation'] = True
            for index, item in enumerate(items):
                _id = item.get('id')
                if _id:
                    if _id.startswith('block') and 'soff' in item.span.a.get('class'):
                        domain['locked'] = False
                    if _id.startswith('aviso') and 'soff' in item.span.a.get('class'):
                        domain['notifications'] = False
                    if _id.startswith('whoIS') and 'soff' in item.span.a.get('class'):
                        domain['private_whois'] = False
                    if _id.startswith('autoRenew') and 'soff' in item.span.a.get('class'):
                        domain['automatic_renovation'] = False
                if 'Fecha de' in item.strong.text:
                    domain['date_created'] = remove_shit(item.span.text.strip())
                if 'Auth Code' in item.strong.text:
                    domain['auth_code'] = item.span.text
                if 'hasta:' in item.strong.text:
                    domain['date_valid'] = remove_shit(item.span.text.strip())
                if index == 1 and item.span.text == 'Activo':
                    domain['status'] = True
        domain['records'] = self.get_records(domain)
        return domain

    def detail_list(self):
        _list = []
        for domain in self.summary:
            if domain['provider'] == 'cdmon':
                _list.append(domain)
            else:
                domain = self.get_details(domain)
                _list.append(domain)
        c = Collection(_list)
        return c

    def get_nameservers(self, domain):
        _list = []
        one_domain = self.index_url + '/es/dominios/dns'
        od_r = self.s.get(one_domain, params={'dades[dom]':domain['canonical_name']})
        raw = od_r.text
        soup = BeautifulSoup(raw, "lxml")
        items = soup.find_all('li', role="listitem")
        for item in items:
            _list.append(item.span.text)
        return _list

    def get_domain_id(self, domain):
        one_domain = self.index_url + '/es/dominios/dns'
        od_r = self.s.get(one_domain, params={'dades[dom]':domain['canonical_name']})
        soup = BeautifulSoup(od_r.text, "lxml")
        provider_id = soup.find_all('input', attrs={"name" : "dades[id]"})
        if len(provider_id) > 0:
            return provider_id[0]['value']

    def set_nameservers(self, domain, nameservers=[]):
        if len(nameservers) > 0:
            one_domain = self.index_url + '/es/dominios/dns'
            domain_name = domain['canonical_name']       
            callback = {
                'action': 'desarDnsDomini',
                'dades[optdns]': '1',
                'dades[hash]': self.ourhash,
                'dades[id]': self.get_domain_id(domain),
            }
            for i, nameserver in enumerate(nameservers):
                if len(nameserver) > 0:
                    e = i + 1
                    callback['dades[selectdns][DNS_2_%s]' % e] = ''
                    callback['dades[servdns][DNS_1_%s]' % e] = nameserver
            r = self.s.post(one_domain, data=callback)
        return self.get_nameservers(domain)

    def get_records(self, domain):
        _list = []
        one_domain = self.index_url + '/es/dns/listado-registros'
        od_r = self.s.get(one_domain, params={'dades[dom]':domain['canonical_name']})
        raw = od_r.text
        soup = BeautifulSoup(raw, "lxml")
        main_domain = soup.find('div', class_="txt").strong.text
        main = soup.find('div', class_="panel-list-body")
        for tbody in main.table.find_all('tbody'):
            record_type = tbody.get('id').split('-')[-1]
            for tr in tbody.find_all('tr'):
                is_record = False
                try:
                    record_id = tr.get('id').split('-')[1]
                    is_record = True
                except: pass
                if is_record == True:
                    cells = tr.find_all('td')
                    if hasattr(cells[0].label, 'input'):
                        record_id = cells[0].label.input['value']
                    host = cells[1].strong.text
                    record = cells[2].strong.text
                    ttl = False
                    priority = ''
                    if record_type in ['TXT','SPF']:
                        record = '"%s"' % cells[2].strong.text
                    elif record_type == 'MX':
                        priority = cells[3].strong.text
                    _dict = {'id': record_id, 'record_type': record_type, 'host': host, 'record': record, 'priority': priority, 'ttl': ttl}
                    _list.append(_dict)
        c = Collection(_list)
        return c

    def delete_all_records(self, domain):
        """ Not working yet"""
        pass

    def delete_record(self, domain, record):
        callback = {
            'dades[hash]': self.ourhash,
            'dades[id]': domain['canonical_name'],
            'dades[tipus]': record['record_type'],
            'dades[sub_id]': record['id'],
            'action': 'esborrarRegistre',
        }
        r_delete_record = self.s.post(self.index_url + self.domains_url_subfix, data=callback)
        domain['records'] = self.get_records(domain)
        logging.info("Record deleted for %s" % domain['name'])
        return domain

    def parse_all(self):
        services_payload = {
            'action':'loadServices',
            'dades[alpha]':'tots',
            'dades[hash]':self.ourhash,
            'dades[nom]':'',
            'dades[order][column]':1,
            'dades[order][type]':'asc',
            'dades[page]':1,
            'dades[type]':0,
            'dades[view]':1000,
            }
        services_list_r = self.s.post(self.services_url, services_payload)
        raw = services_list_r.text
        soup = self.get_soup(hydrate(raw))
        allrows = soup.find_all('tr')
        _list = []       
        for r in allrows:
            _id = None
            try:
                _id = clean_string(r['id'].split("-")[-1])
            except: pass
            cells = r.find_all('td')
            if len(cells) == 3:
                dtend_span = cells[1].find('span', attrs={"class":"dtend"})
                date = u''
                if dtend_span:
                    date = remove_shit(clean_string(dtend_span.text.split("  ")[-1]))
                name = clean_string(cells[1].div.a.get('href')).split('=')[-1]

                #~ canonical_name = clean_string(cells[1].a.get('href')).split('=')[-1]
                canonical_name = name
                slug =  slugify(unicode(name.replace('.','_')))
                _dict = {'id': _id,'name': name, 'canonical_name': canonical_name, 'provider': 'cdmon', 'slug': slug,'date':date}
                logging.debug('Found in CDMON %s' % name)
                if 'alta' in cells[1].text:
                    _dict['provider'] = 'other'
                _list.append(_dict)
            #~ else:
                #~ print(r)
        c = Collection(_list)
        return c
