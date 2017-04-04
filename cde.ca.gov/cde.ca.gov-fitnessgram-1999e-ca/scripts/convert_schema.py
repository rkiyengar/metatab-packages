#
# Using an old schema file from Ambry, generate Metatab schemas. These schemas
# have one table for multiple resources. 

import csv
import six
from collections import defaultdict
from os.path import join, dirname
from metatab import MetatabDoc

schemas = defaultdict(list)

doc = MetatabDoc(join(dirname(__file__),'..','metadata.csv'))

seen_tables = set()

with open(join(dirname(__file__),'ambry_schema.csv')) as f:
    r = csv.DictReader(f)
    
    for row in r:
        schemas[row['table']].append(row)

type_map = {
    float.__name__: 'number',
    int.__name__: 'integer',
    six.text_type.__name__: 'string',
    six.binary_type.__name__: 'text',

}

for k, v in schemas.items():
    
    r = doc.resource(k)
    
    schema_name = r['schema'].value
    
    if schema_name in seen_tables:
        continue
    

    table = doc['Schema'].new_term('Table', schema_name )
    
    print("Table ", k, r['schema'].value)
    for c in v:
        print("Table.Column", c['source_header'], c['dest_header'], c['datatype'], c['description'] )
        
        table.new_child('Column', c['source_header'],
                                    datatype=type_map.get(c['datatype'], c['datatype']),
                                    altname=c['dest_header'])
        
    
    
    seen_tables.add(schema_name )
    
doc.write_csv()