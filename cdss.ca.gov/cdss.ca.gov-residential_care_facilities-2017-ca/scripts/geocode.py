#!/usr/bin/env python
#
# Geocode the facilities  records, using old geocode records when they exist. 

import requests 
from six import StringIO
from os import environ
import csv
import sys
import json
import metatab as mt
from itertools import islice
from geoid.acs import Tract
from requests.exceptions import Timeout
from rowgenerators import SourceError
from metatab import MetatabError

doc = mt.MetatabDoc(environ['METATAB_DOC'])

##
## Load old geocodes, to save time and remote resources
## 

old_url='http://s3.amazonaws.com/library.metatab.org/{}.csv'.format(doc.as_version('-1').find_first_value('Root.Name'))

old_geo = {}

try:
    for row in mt.open_package(old_url).resource('geocodes').iterdict:
    
        try:
            ui = int(row['unique_id'])
            row['unique_id'] = ui
            old_geo[ui] = row
        except ValueError:
            # Erroroneous rows, have 'unique_id' == 'Unique'
            pass
except (SourceError, MetatabError) as e:
    print("Failed to load old geocodes", e, file=sys.stderr)
    
    
geocoder_header = 'unique_id input_address match quality match_address latlon tiger_id side_of_street state_fips county_fips tract_fips block_fips'.split()

out_header = 'unique_id input_address match quality match_address lat lon tiger_id side_of_street state_fips county_fips tract_fips block_fips tract_geoid'.split()
 
w = csv.DictWriter(sys.stdout, out_header)
 
w.writeheader()

def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())
 
def make_request(rows):
    
    if  len(rows) == 0:
        return
    
    header = "Unique ID, Street address, City, State, ZIP".split(',')
    strio = StringIO()
    sw = csv.writer(strio)
    #sw.writerow(header)
    sw.writerows(rows)
    text = strio.getvalue()
    
    tries = 3
    
    yielded = set()
    
    url = 'https://geocoding.geo.census.gov/geocoder/geographies/addressbatch'

    payload = {
        'benchmark':'Public_AR_Current',
        'vintage':'ACS2013_Current', 
        'returntype': 'geographies'
    }

    files = {'addressFile':  ('report.csv', text) }

    while tries:
        
        try:
            r = requests.post(url, files=files, data = payload, timeout= 2*60)
            r.raise_for_status()
    
            for i, row in enumerate(csv.reader(StringIO(r.text))):
                
                if not tuple(row) in yielded:
                    yield row
                yielded.add(tuple(row))
                
            break
        except Timeout as e:
            tries -= 1
            print("TIMEOUT!", e, file=sys.stderr)
        except Exception as e:
            tries -= 1
            print("ERROR", e, file=sys.stderr)
 
def mkdict(row):
    """Turn a geocoder response row into a well-formed dict"""
    d = dict(zip(geocoder_header, row))
    
    if len(row) > 3:

        try:
    
            try:
                d['lat'], d['lon'] = d['latlon'].split(',')
            except ValueError as e:
                d['lat'], d['lon'] = '',''

            d['tract_geoid'] = str(Tract( int(d['state_fips']), int(d['county_fips']), int(d['tract_fips']) ))
            
            try:
                del d['latlon']
            except Exception as e:
                pass
                
    
        except Exception as e:
            # These appear to be errors associated with quote characters in the addresses, like
            # 366426709,"8430 I AVENUE""", HESPERIA, CA," 92345""",No_Match. There aren't many of
            # them, but they are a problem
            print("ERROR for ", row, e, file=sys.stderr)
    
            d['input_address'] = ''
            d['match'] = 'Parse Error'
           
    return d
            
# Chunk the facilities CSV file into smaller blocks. The Census geocoder will only 
# accept 1000 lines at a time, but we'll send smallerfiles. 

def chunked_geocode(doc):

    # Header for the file submitted to the geocoder
    
    row_n = 0
    
    request_rows = []

    
    for row in doc.resource('facilities').iterdict:

        # If the row is in the old geocodes, yield it immediately
        try:
            if int(row['facility_number']) in old_geo:
                old_row = old_geo[int(row['facility_number'])]
                yield row_n, False, old_row
                row_n += 1
                continue
        except ValueError:
            pass

        request_rows.append([row['facility_number'], 
                     row['facility_address'], 
                     row['facility_city'], 
                     row['facility_state'],
                     row['facility_zip']])
        
        if len(request_rows) > 250:
            
            for row in make_request(request_rows):
                # row colums are:
                # unique_id input_address match quality match_address latlon tiger_id side_of_street state_fips county_fips tract_fips block_fips
                yield row_n, True, mkdict(row)
                row_n += 1
                
            request_rows = [];

            
    for row in make_request(request_rows):
        # row colums are:
        # unique_id input_address match quality match_address latlon tiger_id side_of_street state_fips county_fips tract_fips block_fips
        yield row_n, True, mkdict(row)
        row_n += 1
            
     
for row_n, was_geocoded, row in chunked_geocode(doc):
    
    w.writerow(row)



