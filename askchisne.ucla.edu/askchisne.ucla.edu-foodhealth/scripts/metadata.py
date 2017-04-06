#! /usr/bin/env python3 -u
# Dump the AskCHISNE metadata, for the entire collection of variables and geographies

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


if not api_key:
    sys.stderr.write("ERROR: Must set ASKCHIS_API_KEY environmental variable ")
    sys.exit(1)

csv_headers = 'dataSetId year name sourceVariable geoVariableMetadataId pooling unit visibility label ageGroup responseLabel topic  description'.split()

w = csv.DictWriter(sys.stdout, csv_headers)
w.writeheader()

headers = { 'Ocp-Apim-Subscription-Key': api_key }

params = urlencode({})

conn = http.client.HTTPConnection('askchisne.azure-api.net')
conn.request("GET", "/api/metadata?{}".format(params), "{body}", headers)
response = conn.getresponse()
data = response.read()

d = json.loads(data.decode('utf8'))
conn.close()

for e in d:
    w.writerow(e)