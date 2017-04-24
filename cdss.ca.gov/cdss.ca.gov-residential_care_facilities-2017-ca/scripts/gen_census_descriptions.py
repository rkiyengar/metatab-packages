
import json 
with open('data//acs2015_5yr_B17024_14000US06073008359.json  ') as f:
    d = json.load(f)

    cols = []
    
    for table_name, table in d['tables'].items():
        for c_name, col in table['columns'].items():

            cols.append((c_name, col['name']))
            cols.append((c_name+'_error', "Error margin for "+c_name+', '+col['name']))
    
for c in sorted(cols):
    print(c)
    
import csv

with open('census_descriptions.csv','w') as f:
    csv.writer(f).writerows(sorted(cols))
