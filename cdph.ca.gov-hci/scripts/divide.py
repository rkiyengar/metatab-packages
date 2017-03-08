#!/usr/bin/env python

""" Divide the combined package into seperate tables"""

import sys

from metatab import Package, CsvPackage
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


name_map = {
    'datafile': 'data-',
    'suplimentarydata': 'supdata-',
    'documentation': 'doc-',
    'datadictionary': 'dd-',
}


for r in list(p.resources()):

    for c in (r.find_first('StartLine'), r.find_first('HeaderLines'), r.find_first('Encoding')):
        if c is not None:
            r.remove_child(c)


    packs[r.schema].sections.resources.add_term(r)
  

for r in list(p.resources(term=['Root.Datadictionary','Root.Documentation'], section='Documentation')):
    
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

    t = p.doc.find_first('Root.Table', name)

    if t:
        package.sections.schema.args += ['Widthformat','Coding']
        package.sections.schema.add_term(t)

    prt("Saving package ", package.doc.find_first_value('root.name'))
    package.save()








