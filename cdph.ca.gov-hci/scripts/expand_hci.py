#!/usr/bin/env python

import sys
from metapack import Package, CsvPackage, Resource
from metapack.util import parse_url_to_dict, unparse_url_dict
from collections import defaultdict
from rowgenerators import RowGenerator, DictRowGenerator
from six import text_type
from rowgenerators.sourcespec import decompose_url


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


ep = CsvPackage(callback=prt)

ep.sections.root.new_term('Title', 'All HCI Files')
ep.sections.root.new_term('Name', 'hci-expanded')

r = ep.sections.resources # Make sure the section exists
r.args.append('Segment')
r = ep.sections.contacts # Make sure the section exists
r = ep.sections.documentation # Make sure the section exists
ep.doc.new_section('Schema', 'DataType WidthFormat Description Coding'.split())

groups = defaultdict(list)

# IN the first pass add all of the resources by their given URL. In many cases, this will expand
# the resource to all of the files in a ZIP, or all of the sheet in an XLS. Later, we'll cull  unnecessary
# resources.

def multiget(d, *args):

    for k in args:
        try:
            return d[k]
        except KeyError:
            pass

    raise KeyError("None of keys for {} ".format(args))

datatypes = {
    'Num': 'number',
    'N': 'number',
    'T': 'text',
    'D/T': 'datetime',
    'Char': 'text',
    'C': 'text'

}

for i, r in enumerate(p.datafiles):

    if not r.term.term_is('root.Datafile'):
        continue

    r.url = unparse_url_dict(rp_parts, path=r.url)

    try: r.documentation = unparse_url_dict(rp_parts, path=r.documentation)
    except AttributeError: pass

    schema = r.schema # Should also be the same

    try: space = r.space
    except AttributeError: space = None

    try: time = r.time
    except AttributeError: time = None

    try: description = r.description
    except AttributeError: description = None

    name = '-'.join(str(e) for e in (r.schema, space, time) if e)

    added = ep.add_resource(r.url, schema=r.schema, name=name, description=description, space= space, time= time)

    if r.documentation:
        ep.sections.documentation.new_term('Documentation', r.documentation, schema=schema, description=description)

    for t in added:

        try:
            r = Resource(t, ep)
        except AttributeError as e:
            warn("Failed for : {}, {}".format(t, e))
            continue

        if "Dictionary" in r.url:

            t = ep.sections.schema.new_term("Root.Table", r.schema)

            prt("Generating DD for '{}' ".format(r.url))

            for row in DictRowGenerator(RowGenerator(r.url)):
                try:

                    datatype = datatypes.get(text_type(row['Type']).strip(),text_type(row['Type']).strip())
                    if multiget(row,'Width/Format', 'Width') == 'integer':
                        datatype = 'integer'

                    t.new_child('Table.Column',
                                multiget(row,'Variable','Name'),
                                datatype=datatype ,
                                widthformat=multiget(row,'Width/Format', 'Width'),
                                description=row['Definition'],
                                coding=multiget(row,'Coding','Coding/Comments')
                                )
                except KeyError as e:
                    warn("Different keys for '{}': {}. Keys are: {} ".format(schema, e, row.keys()))

            r.term.term='DataDictionary'

        elif "Filter" in r.url or 'READ' in r.url or 'Guide' in r.url:
            r.term.term = "Documentation"

        elif 'CHISCounties' in r.url or 'MPO' in r.url:
            r.term.term = "SuplimentaryData"
        else:
            pass # These should be normal data files.



    ep.save('expanded.csv')
