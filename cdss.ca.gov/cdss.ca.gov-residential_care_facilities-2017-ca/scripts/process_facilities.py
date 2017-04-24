#!/usr/bin/env python
"""Load the Facilities list from the web and re-emit it, with the
variable columns replaced with a JSON array"""

import metatab as mt
import sys
import csv
import json
from os import environ
from itertools import islice

props = json.loads(environ['PROPERTIES'])
doc = mt.MetatabDoc(props['metatab_doc'])

w = csv.writer(sys.stdout)

def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())

# Complain details is a JSON array of tuples, with these values: 
# (Date, #Sub Aleg, # Inc Aleg, #Unf Aleg, # TypeA, # TypeB )

# Using the .row_generator directly because the rows have a variable width, so we need a 
# raw
for i, row in enumerate(doc.resource('raw_facilities', term='Root.Reference').row_generator):

    main_row, remainder = row[:36], row[36:]
 
    if len(remainder) % 6 == 0:
        chunks = list(chunk(remainder, 6))
    else:
        chunks = []

    if i == 0:  
        w.writerow(main_row + ['complaint_details'])
    else:
         w.writerow(main_row + [json.dumps(chunks)])