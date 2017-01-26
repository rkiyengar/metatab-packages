#!/usr/bin/env python

import sys
from metapack import Package, ExcelPackage
from metapack.util import parse_url_to_dict, unparse_url_dict
from collections import defaultdict
from rowgenerators import RowGenerator, DictRowGenerator



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

root_url = p.doc.find_first_value('Root.Downloadpage', section='Resources')
rp_parts = parse_url_to_dict(root_url)

groups = defaultdict(list)

for r in p.datafiles:

    if not r.term.term_is('root.Datafile'):
        continue

    r.url = unparse_url_dict(rp_parts, path=r.url)

    try:
        r.documentation = unparse_url_dict(rp_parts, path=r.documentation)
    except AttributeError:
        pass

    groups[r.schema].append(r)

for k, v in groups.items():

    print(k)

    ep = ExcelPackage(callback=prt)

    desc = None
    documentation = None
    for e in v:

        ep.add_resource(e.url)

        try:
            desc = e.description # Same for all of them
        except:
            pass

        try:
            documentation = e.documentation # Same for all of them
        except:
            pass

        table = e.table # Should also be the same

    if documentation:
        ep.sections.documentation.new_term('Documentation', documentation)

    ep.sections.root.new_term('Title', desc)
    ep.sections.root.new_term('Name', table)

    ep.doc.new_section('Schema', 'DataType WidthFormat Description Coding'.split())

    t = ep.sections.schema.new_term("Root.Table", table)
    r = ep.sections.resources # Make sure the section exists

    for r in ep.resources:
        if "DataDictionary" in r.url:
            for row in DictRowGenerator(RowGenerator(r.url)):
                try:
                    t.new_child('Table.Column',
                                row.get('Variable', row['Name']),
                                datatype=row['Type'],
                                widthformat=row['Width/Format'],
                                description=row['Definition'],
                                coding=row['Coding']
                                )
                except KeyError as e:
                    warn("Different keys for '{}': {} ".format(table, e))


            ep.doc.remove_term(r.term)

        elif ("Filter" in r.url
               or 'CHISCounties' in r.url
               or 'MPO_CountyList' in r.url
               or 'READ' in r.url):
            ep.doc.remove_term(r.term)
        else:
            r.schema = table


    ep.save()

    break



