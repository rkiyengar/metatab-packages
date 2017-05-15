#!/usr/bin/env python

import sys
import csv
from os import environ
import metatab as mt
from address_parser import Parser
import difflib 
import nltk
import re
from metaphone import doublemetaphone
from collections import Counter, defaultdict

#nltk.download("stopwords")
from nltk.corpus import stopwords

w = csv.writer(sys.stdout)

parser = Parser()

doc = mt.MetatabDoc(environ['METATAB_DOC'])

hashes = {}


def make_name_hash(row):
    name = row['facility_name'].replace("'", '')


    filtered_name = [word for word in name.lower().split() 
                    if word not in stopwords.words('english') and re.match('^[\w-]+$', word)]

    meta_name = '-'.join([doublemetaphone(w)[0] for w in filtered_name])
    
    return meta_name
    
def make_fac_address(row):
    return parser.parse(row['facility_address'], row['facility_city'], row['facility_state'], row['facility_zip'])

def make_alwp_address(row):
    return parser.parse(row['address'], row['city'], 'CA' , row['zip'])
    
 
def clean_str(s):
     import re
     return re.sub(r'^a-zA-Z0-9', '' , s).lower()
     
addresses = defaultdict(set)
names = defaultdict(set)
hashes = []
rows = dict()

for row in  doc.resource(name='facilities', term='Root.Sourcefile').iterdict:
    
    if row['facility_status'] != 'LICENSED':
        continue

    addresses[make_fac_address(row).hash].add(row['facility_number'])
    names[clean_str(row['facility_name'])].add(row['facility_number'])
    rows[row['facility_number']] = row
    
def similarity(a, b):
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a, b).ratio()

def similarities(this_name, names):
    
    hits = []
    
    for fname, numbers in names.items():
        s = similarity(clean_str(this_name), clean_str(fname))
        
        if s > .8:
            hits.append( (s,fname,numbers))
    
    return list(reversed(sorted(hits)))
    
def address_match(row, addresses):
    fn = addresses.get(make_alwp_address(row).hash)
    
    if fn:
        row = rows.get(list(fn)[0])
    
        return row
    
    return None
    
    
def best_match(row):
    
    
    adr_row = address_match(row, addresses)
    
    if adr_row:
        return adr_row
        
    s = similarities(name,  names)

    if s and len(s) > 0:
        s,fname,numbers = s[0]
        
        return rows.get(list(numbers)[0])
    
    
for row in  doc.resource(name='alwp-list').iterdict:
    name = row['facility_name']
    
    bn = best_match(row)
    
    if bn:
         fname = bn['facility_name']
         fnum = bn['facility_number']
         adr = make_fac_address(bn)
         adr_text = str(adr)
         
    else:
        fname = None
        fnum = None
        adr_text = None
        
        
    w.writerow([name, fname, fnum, adr_text])
         
    
         
    
    
    
   