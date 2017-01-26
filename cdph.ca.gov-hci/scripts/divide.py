#!/usr/bin/env python

""" Divide the combined package into sepectate tables"""

import sys

from metapack import Package, CsvPackage
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


for r in list(p.resources):

    for c in (r.term.find_first('StartLine'), r.term.find_first('HeaderLines'), r.term.find_first('Encoding')):
        if c is not None:
            r.term.remove_child(c)

    r.name = name_map.get(r.term.record_term_lc,'')+r.name

    if r.term.term_is('Datafile') or r.term.term_is('Suplimentarydata'):
        packs[r.schema].sections.resources.add_term(r.term)
    else:
        packs[r.schema].sections.documentation.add_term(r.term)


for name, package in packs.items():

    r = next(package.resources)
    package.sections.root.new_term('Name', name)
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








