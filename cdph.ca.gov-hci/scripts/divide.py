#!/usr/bin/env python

""" Divide the combined package into seperate tables"""

import sys

from metatab import Package, CsvPackage, open_package
from collections import defaultdict


def prt(*args):
    print(*args)

def warn( *args):
    print('WARN:',*args)

def err(*args):
    import sys
    print("ERROR:", *args)
    sys.exit(1)

if len(sys.argv) < 2:
    err("Must provide a reference to a package")

bf = sys.argv[1]

p = Package(bf)

packs = defaultdict(CsvPackage)

prt("Opening xwalk package")
xwalk = open_package('http://library.metatab.org/zip/cdph.ca.gov-county_crosswalk-ca-3.zip')
xwalk_table = xwalk.find_first('Root.Table')
xwalk_table.value = 'county-xwalk'

name_map = {
    'datafile': 'data-',
    'suplimentarydata': 'supdata-',
    'documentation': 'doc-',
    'datadictionary': 'dd-',
}

prt("Loading resources")
for r in list(p.resources()):

    for c in (r.find_first('StartLine'), r.find_first('HeaderLines'), r.find_first('Encoding')):
        if c is not None:
            r.remove_child(c)

    if r.term_is('Root.Datafile'):
        r.value = r.value.replace('https','http')
        packs[r.schema].sections.resources.add_term(r)
  

for r in list(p.resources(term=['Root.Datadictionary','Root.Documentation'], section='Documentation')):
    r.value = r.value.replace('https','http')
    packs[r.schema].sections.documentation.add_term(r)
    

for name, package in packs.items():

    try:
        r = next(package.resources())
    except KeyError as e:
        warn(name, e)
        continue
    n = package.sections.root.new_term('Name', name)
    n.new_child('Dataset',name)
    n.new_child('Version',1)
    n.new_child('Origin','cdph.ca.gov')
    package.sections.root.new_term('Description', r.description)
    package.sections.resources.args.remove('StartLine')
    package.sections.resources.args.remove('HeaderLines')
    package.sections.resources.args.remove('Encoding')

    package.sections.resources.sort_by_term()
    package.sections.documentation.sort_by_term()

    package.sections.resources.new_term('Datafile',
        'metatab+http://library.metatab.org/cdph.ca.gov-county_crosswalk-ca-2#county_crosswalk',
        name=xwalk_table.value,
        description='Crosswalk between California counties, MPO areas, CHIS regions and FIPS codes.')

    t = p.doc.find_first('Root.Table', name)

    if t:
        package.sections.schema.args += ['Widthformat','Coding']
        package.sections.schema.add_term(t)

    prt("Saving package ", package.doc.find_first_value('root.name'))

    package.sections.schema.move_term(xwalk_table)
    
    package.save()








