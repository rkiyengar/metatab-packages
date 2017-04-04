#
# Using a metatab file created by hand from the Ambry schema, update the
# main Metatab file 

import csv
import six
from collections import defaultdict
from os.path import join, dirname
from metatab import MetatabDoc

schemas = defaultdict(list)

doc = MetatabDoc(join(dirname(__file__),'..','metadata.csv'))

sch = MetatabDoc(join(dirname(__file__),'ambry_metatab_schema.csv'))

for t in doc.find('Root.Table'):
    scht = sch.find_first('Root.Table', value=t.value)
    
    for c in t.children:
        schc = scht.find_first('Table.Column', value=c.value)

        c['ValueType'] = schc.properties.get('valuetype')
        c['DataType'] = schc.properties.get('datatype')
        c['Transform'] = schc.properties.get('transform')
        c['Description'] = schc.properties.get('description')
        
 
#import json
#print(json.dumps(doc.as_dict(), indent=4))
    
doc.write_csv()