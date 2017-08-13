from getout.api import CDMON

"""
Change record values
"""

standard_template = [
    {'record_type': 'CNAME', 'host': '*', 'record': 'example.org', 'value': False, 'weight': False, 'priority': False},
    {'record_type': 'A', 'host': '@', 'record': '195.154.200.103', 'value': False, 'weight': False, 'priority': False},
]

"""
Change everything to your needs
"""
standard_email_template = [
    {'record_type': 'TXT', 'host': '@', 'record': False, 'value': "v=spf1 mx a ptr ?all", 'weight': False, 'priority': False,},
    {'record_type': 'MX', 'host': '@', 'priority': '5', 'record': 'mail.example.org', 'value': False, 'weight': False,},
    {'record_type': 'CNAME', 'host': 'correo', 'record': 'mail.example.org', 'value': False, 'weight': False, 'priority': False},
    #~ {'record_type': 'CNAME', 'host': 'smtp', 'record': 'mail2.getcloud.info', 'value': False, 'weight': False, 'priority': False},
    #~ {'record_type': 'CNAME', 'host': 'imap', 'record': 'mail2.getcloud.info', 'value': False, 'weight': False, 'priority': False},
]

"""
New provider nameservers
"""
nameservers=['ns1.another.com','ns2.another.com','ns3.another.com']

def my_domains():
    """ You can call all cdmon using cdmon.get_summary()"""
    return [
        {'name': 'mycustomersite.com', 'standard': True, 'email': True, 'slug': 'mycustomersite'}
    ]

cdmon = CDMON(user="yourcdmonuser",password="yourcdmonpassword")

def add_empty_domain():
    for entry in my_domains():
        print entry
        cdmon.add_domain(entry['name'])
        
def modify_one_domain():
    domain = cdmon.get("postalcloud.net")
    print(domain)
    exists = domain['records'].filter(record_type__exact='A',host__exact='w2')
    if len(list(exists)) == 0:
        record = ('A', 'w2', '127.0.0.1',False,False,False,)
        cdmon.set_record(domain, *record)
    else:
        print("exists")
modify_one_domain()

def modify_all_domain():
    summary = cdmon.get_summary()

    for entry in get_domains():
        print entry['name']
        zones = list(summary.filter(name__exact=entry['name']))
        if len(zones) > 0:
            zone = zones[0]
            domain = cdmon.get_details(zone)
            print domain
            cdmon.set_nameservers(domain, nameservers=nameservers)
            for record in domain['records']:
                cdmon.delete_record(domain, record)
            template = []
            if entry['standard'] == True:
                template += standard_template
            if entry['email'] == True:
                template += standard_email_template
            if 'records' in entry:
                template += entry['records']
            for new_record in template:
                for k,v in new_record.iteritems():
                    if v is not False and "%s" in v:
                        print "templating!"
                        new_record[k] = v % domain['canonical_name']
                cdmon.set_record(domain, new_record['record_type'], new_record['host'], destination=new_record['record'], value=new_record['value'], weight=new_record['weight'], priority=new_record['priority'])
            print "." * 40
            print entry
            for record in domain['records']:
                print record
