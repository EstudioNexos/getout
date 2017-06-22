from api import CDMON

cdmon = CDMON(user="yourcdmonuser",password="yourcdmonpassword")


""" Fast summary of domains (no records) """

print list(cdmon.get_summary())

""" Everything including records and nameservers """
for val in cdmon.all():
    print val
    print val['slug']
    if 'records' in val:
        for record in val['records']:
            print record
    print "." * 20

