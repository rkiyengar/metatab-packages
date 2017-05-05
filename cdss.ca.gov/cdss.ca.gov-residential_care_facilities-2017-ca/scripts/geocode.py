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
from geoid.census import Tract as CensusTract
from geoid.acs import Tract as AcsTract
from requests.exceptions import Timeout
from rowgenerators import SourceError
from metatab import MetatabError

doc = mt.MetatabDoc(environ['METATAB_DOC'])

## Need to have the facility number -> zip seperately. 

fac_zip = {}

for row in doc.resource('facilities').iterdict:
    fac_zip[row['facility_number']] = row['facility_zip']

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

def make_zip_map():
    """Create a map from zip to track that uses the HUD zip-tract cross walk as a probablilty
    map, with the facility it used as the probability. Using the facility ID makes the mapping stable. """
    zip_xwalk_doc = mt.open_package('http://library.metatab.org/huduser.gov-zip_tract-2016-2.csv')
    zip_xwalk = zip_xwalk_doc.resource('zip-tract')
    zip_xwalk_df = zip_xwalk.dataframe()
    zx_groups = zip_xwalk_df.sort_values('res_ratio').groupby('zip')
    
    def make_single_zip_map_f(groups, zip):
        """Function to create a closure for mapping for a single zip, from an id value to 
         tract"""
        import numpy as np
        import pandas as pd

        # Use the resigential ratios, the portion of the homes in the zip that are in each tract. 
        res_ratios = list(zx_groups.get_group(zip).cumsum().res_ratio)
        tracts = list(zx_groups.get_group(zip).tract)
        
        assert len(res_ratios) == len(tracts)

        def _f(id):
            # Use the end of the ID value to ensure repeadability
            n = float(id%100) / 100.0
            index = np.argmax(pd.Series(res_ratios) > n)

            return tracts[index]

        return _f
    
    f_map = {}
    
    # dict that returns, for each zip, the function to get a tract for the id number. 
    for zp in zx_groups.groups.keys():
        f_map[zp] = make_single_zip_map_f(zx_groups, zp)
        
    # Finally, put it all together in a single closure. 
    def lookup(zip, n):

        try:
            # The map will return a Census geoid, which has 11 charasters, but it is often missing
            # the leading 0, so we have to put it back. Then it much be converted to an 
            # ACS Tract
            census_tract_str =  str(f_map[int(zip)](int(n)%100 / 100.0)).zfill(11)
            return str(AcsTract.parse(census_tract_str))
        except KeyError:
            return None

    return lookup
        
zip_to_tract = make_zip_map() 


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
            
     
from geoid.census import Tract
     
for row_n, was_geocoded, row in chunked_geocode(doc):

    if not row.get('tract_geoid'):
        row['tract_geoid'] = zip_to_tract(fac_zip[int(row['unique_id'])], int(row['unique_id']))
        row['side_of_street'] = None
        row['tiger_id'] = None

    if row['tract_geoid']:
        
        if len(row['tract_geoid']) != 18:
            # It's probably still a Census Tract, so convert it to an Acs tract. 
            row['tract_geoid'] = str(CensusTract.parse(row['tract_geoid'].zfill(11)).convert(AcsTract))
        
        assert(len(row['tract_geoid'])) == 18, row['tract_geoid'] 
        
        t = AcsTract.parse(row['tract_geoid'])
        
        #print(str(t), file=sys.stderr)
        
        row['state_fips'] = t.state
        row['county_fips'] = t.county
        row['tract_fips'] = t.tract
        

    if row.get('state_fips'):
        row['state_fips'] = str(row['state_fips']).zfill(2)
        
    if row.get('county_fips'):
        row['county_fips'] = str(row.get('county_fips')).zfill(3)
    
    try:
        w.writerow(row)
    except:
        print("ERROR ROW: ", row, e, file=sys.stderr)
    
        
        
