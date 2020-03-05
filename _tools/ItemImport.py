#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import codecs
from collections import OrderedDict
import csv
import fnmatch
import json
import os
import sys
import unicodedata

TR_name = {"": ""}
JP_dup = dict()
TR_dup = dict()
TR_explain = dict()
TR_src = dict()
Baddup = list()

csv.register_dialect('pipes', delimiter='|', quoting=csv.QUOTE_NONE)

# error counter
counterr = 0

# Need the json path
if len(sys.argv) < 2:
    print("Where the json folder?")
    sys.exit(os.EX_NOINPUT)


# Need the CSV file
if len(sys.argv) < 3:
    print("Where the item file?")
    sys.exit(os.EX_NOINPUT)

dir = sys.argv[1]
with codecs.open(sys.argv[2], encoding="utf-8") as c:
    CSV = list(csv.reader(c, dialect='pipes', strict=True))

for line in CSV:
    DUP = False
    k = line[0]
    t = line[1]
    d = line[2]
    if (k == t):
        t = ""
    nk = unicodedata.normalize('NFKC', k).lower()
    nt = unicodedata.normalize('NFKC', t)
    if nk in JP_dup:
        print("Item JP name '{}'/'{}' already in with '{}'/'{}'".format(k, nk, JP_dup[nk], t))
        DUP = True
    if t != "":
        if nt in TR_dup:
            print("Item EN name '{}'/'{}' already taken '{}'/'{}'".format(t, nt, TR_dup[nt], k))
            DUP = True
    JP_dup[nk] = k
    TR_dup[nt] = t
    TR_name[k] = t
    if DUP:
        Baddup.append(k)
        Baddup.append(nk)
    if d != "" and k in TR_explain:
        if d != TR_explain[k]:
            print("Item Desc {}/{}".format(k, t))
        elif d != TR_explain[k]:
            TR_explain[k] = d.replace(
                "<br>", "\n").rstrip().replace("\n", "<br>")
    else:
        TR_explain[k] = d.replace("<br>", "\n").rstrip().replace("\n", "<br>")
    if TR_explain[k].count("<br>") >= 4:
        print("item Desc {} is too long".format(k))
    TR_src[k] = "CSV"

json_files = [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_*.txt')
]

json_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Explain_Actor_*.txt')
]

json_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Explain_SkillRing.txt')
]

json_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Explain_System.txt')
]

json_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Name_Actor_MagName.txt')
]

json_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Name_UICharMake_*.txt')
]

for files in json_files:
    with codecs.open(files, mode='r', encoding='utf-8') as json_file:
        change = False
        Explain = False
        try:
            djson = json.load(json_file, object_pairs_hook=OrderedDict)
            for entry in djson:
                if "tr_explain" in entry:
                    Explain = True
                k = entry["jp_text"]
                nk = unicodedata.normalize('NFKC', k).lower()
                t = entry["tr_text"]
                nt = unicodedata.normalize('NFKC', t)
                ok = None
                if Explain:
                    d = entry["tr_explain"]
                else:
                    d = ""

                if k == "":
                    continue
                elif (k in TR_name and TR_src[k] == "CSV"):
                    if TR_name[k] != t and TR_name[k] != "":
                        print("TR name of \'{}\' from \'{}\' to \'{}\'".format(
                            k, t, TR_name[k])
                        )
                        change = True
                    else:
                        TR_name[k] = t

                    TR_src[k] = "JSON"

                    c = d.rstrip().replace("\n", "<br>")
                    if Explain and TR_explain[k] != c and TR_explain[k] != "":
                        print("TR desc of \'{}\' from \'{}\' to \'{}\'".format(
                            k, c, TR_explain[k])
                        )
                        change = True
                    else:
                        TR_explain[k] = d
                elif (k not in TR_name and nk in JP_dup):
                    ok = k
                    k = JP_dup[nk]
                    print("Could not find '{}' but found '{}'".format(ok, k))
                    if TR_name[k] != t and TR_name[k] != "":
                        print("TR name of \'{}\' from \'{}\' to \'{}\'".format(
                            ok, t, TR_name[k]))
                        change = True
                    TR_name[ok] = TR_name[k]

                    TR_src[ok] = "JSON"
                    TR_src[k] = "JSON"

                    if Explain and TR_explain[k] != c and TR_explain[k] != "":
                        print("TR desc of \'{}\' from \'{}\' to \'{}\'".format(
                            k, c, TR_explain[k])
                        )
                        change = True
                    TR_explain[ok] = TR_explain[k]

                    k = ok
                else:
                    TR_name[k] = t
                    TR_src[k] = "NEW"
                    TR_explain[k] = d

                if nk in JP_dup and JP_dup[nk] != k and ok is None:
                    print("Item JP name '{}'/'{}' already in with '{}'/'{}'".format(k, nk, JP_dup[nk], t))
                    counterr += 1
                else:
                    JP_dup[nk] = k

                if t != "":
                    if nt in TR_dup and TR_dup[nt] != t and ok is None:
                        print("Item EN name '{}'/'{}' already taken '{}'/'{}'".format(t, nt, TR_dup[nt], k))
                        counterr += 1
                    else:
                        TR_dup[nt] = t
            if change:
                print("Updating {}.txt".format(
                    os.path.splitext(os.path.basename(files))[0]))
                if Explain:
                    djson = [
                        OrderedDict([
                            ('assign', e["assign"]),
                            ('jp_text', e["jp_text"]),
                            ('tr_text', TR_name[e["jp_text"]]),
                            ('jp_explain', e['jp_explain']),
                            ('tr_explain', TR_explain[e["jp_text"]].replace(
                                "<br>", "\n").rstrip())
                        ])
                        for e in djson
                    ]
                else:
                    djson = [
                        OrderedDict(
                            [
                                ('assign', e["assign"]),
                                ('jp_text', e["jp_text"]),
                                ('tr_text', TR_name[e["jp_text"]])
                            ]
                        )
                        for e in djson
                    ]
                with codecs.open(
                    files, mode='w+', encoding='utf-8'
                ) as json_file:
                    json.dump(
                        djson, json_file, ensure_ascii=False,
                        indent="\t", sort_keys=False)
                    json_file.write("\n")
        except ValueError as e:
            counterr += 1
            print("%s: %s" % (files, e))


others = list()

for e in TR_src:
    if TR_src[e] == "CSV":
        others.append(e)

others = sorted(others)

ojson = list()

JP_explain = dict()

for k in Baddup:
    JP_explain[k] = "DUP"
    nk = unicodedata.normalize('NFKC', k).lower()
    JP_explain[JP_dup[nk]] = "DUP"

for e in others:
    if e not in JP_explain:
        JP_explain[e] = ""
    ojson += [
        OrderedDict(
            [
                ('jp_text', e),
                ('tr_text', TR_name[e]),
                ('jp_explain', JP_explain[e]),
                ('tr_explain', TR_explain[e].replace("<br>", "\n")),
                ('assign', 0)
            ]
        )
    ]

with codecs.open(os.path.join(dir, "Items_Leftovers.txt"), mode='w+', encoding='utf-8') as json_file:
    json.dump(
        ojson, json_file, ensure_ascii=False, indent="\t", sort_keys=False)
    json_file.write("\n")
    print("Left with {} leftover items".format(len(ojson)))

if counterr > 0:
    sys.exit("Issues found")
