#! /usr/bin/env python3 -u

import http.client, urllib.request, urllib.parse, urllib.error, base64
from urllib.parse import urlencode, quote_plus
import json

from string import ascii_uppercase
import sys
import csv
from os import getenv, environ
import json
import select


try:
    props = json.loads(getenv('PROPERTIES'))
except TypeError:
    props = {}
    
api_key = getenv("ASKCHIS_API_KEY")

geo_type = props.get("geotype", getenv("ASKCHIS_GEO_TYPE"))
var_name = props.get("varname", getenv("ASKCHIS_VAR_NAME"))

if not api_key:
    sys.stderr.write("ERROR: Must set ASKCHIS_API_KEY environmental variable ")
    sys.exit(1)

if not geo_type:
    sys.stderr.write("ERROR: Must set geotype property or ASKCHIS_GEO_TYPE environmental variable ")
    sys.exit(1)

if not var_name:
    sys.stderr.write("ERROR: Must set varname property or ASKCHIS_VAR_NAME environmental variable ")
    sys.exit(1)

w = csv.writer(sys.stdout)

w.writerow(' geoid geoname population estimate std_err ci_l95 ci_u95 cv mse supression'.split())

headers = { 'Ocp-Apim-Subscription-Key': api_key }

params = urlencode({
    # Request parameters
    'attributes': 'population,estimate,SE,CI_LB95,CI_UB95,CV,MSE',
    'geoType': geo_type,
    'year': '2014',
})


conn = http.client.HTTPConnection('askchisne.azure-api.net')
conn.request("GET", "/api/variable/{}?{}".format(var_name, params), "{body}", headers)
response = conn.getresponse()
data = response.read()

d = json.loads(data.decode('utf8'))
conn.close()

geo = d[0]['geographies']

for g in geo:
    
    attr =  g['attributes']
    
    if attr[0] == 'Pop. < 500':
        attr[0] = None
    
    try:
        w.writerow([g['geoId'], g['geoName']] + attr + [g['suppressionReason']])
    except BrokenPipeError:
        sys.stderr.write("Broken Pipe")
        sys.exit(1)