#!/usr/bin/env python

# Unique ID, Street address, City, State, ZIP
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

props = json.loads(environ['PROPERTIES'])
doc = mt.MetatabDoc(props['metatab_doc'])

def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())
 
def make_request(text):
    
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
    
            for row in csv.reader(StringIO(r.text)):
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
            
# Chunk the facilities CSV file into smaller blocks. The Census geocoder will only 
# accept 1000 lines at a time, but we'll send smallerfiles. 

def chunked_geocode(doc):
    row_n = 0
    tries = 3

    if False:
        
        with open('/tmp/chunks.txt') as f:

            for chunk_n, chunk_i, row_n, *row in csv.reader(f):
                yield chunk_n, chunk_i, row_n, row
    else:
        
    
        for chunk_n, ch in enumerate(chunk(doc.resource('facilities').iterdict,250)):

            strio = StringIO()
            sw = csv.writer(strio)

            # Header for submitted file
            header = "Unique ID, Street address, City, State, ZIP".split()
            sw.writerow(header)

            for row in ch:
                sw.writerow([row['facility_number'], 
                             row['facility_address'], 
                             row['facility_city'], 
                             row['facility_state'],
                             row['facility_zip']])

            text = strio.getvalue()

            for chunk_i, row in enumerate(make_request(text)):
                yield chunk_n, chunk_i, row_n, row
                row_n += 1
            
            
if False:
    
    with open('/tmp/chunks.txt', 'w') as f:
        chunk_writer = csv.writer(f)
    
        for chunk_n, chunk_i, row_n, row in chunked_geocode(doc):
            out_row = [chunk_n, chunk_i, row_n] + row
            print(out_row, file=sys.stderr)
            chunk_writer.writerow(out_row)

 
    sys.exit(0)
     
header = 'unique_id input_address match quality match_address lat lon tiger_id side_of_street state_fips county_fips tract_fips block_fips tract_geoid'.split()
 
w = csv.writer(sys.stdout)
 
w.writerow(header)

for chunk_n, chunk_i, row_n, row in chunked_geocode(doc):


    if len(row) > 3:
        try:
            lat, lon = row[5].split(',')
        except ValueError as e:
            lat, lon = '',''
            
        try:
            tract_geoid = str(Tract( int(row[8]), int(row[9]), int(row[10]) ))
            out_row = row[:5] + [lat, lon] + row[6:] + [tract_geoid]
        except Exception as e:
            # These appear to be errors associated with quote characters in the addresses, like
            # 366426709,"8430 I AVENUE""", HESPERIA, CA," 92345""",No_Match. There aren't many of
            # them, but they are a problem
            print("ERROR for ", row, e, file=sys.stderr)
            
            out_row = [row[0],'','Parse Error'] + ['']*(len(header) - 3)
            
        
    else:
        out_row = row +['']*(len(header) - len(row))
        

    print(chunk_n, chunk_i, row_n,out_row, file=sys.stderr)
    w.writerow(out_row)



