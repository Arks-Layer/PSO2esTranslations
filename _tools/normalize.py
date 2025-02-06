#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import codecs
from collections import OrderedDict
import fnmatch
import json
import os
import sys
import unicodedata

quick = {
    "*": "＊",  # Undo normalize of Asterisk
    "¥": "￥",  # Undo normalize of Yen
    "『": "\"", "』": "\"",  # Use English Quotes
    "–": "-", "‒": "-",  # Replaces DASHs with HYPHEN-MINUS
    "​": "",  # ZERO WIDTH SPACE need to gone from this world
    "ō": "ou", "ū": "uu",  # MACRONs are not supported
    "\0": "\0"
}

# error counter
counterr = 0

# Need the json path
if len(sys.argv) < 2:
    dir = "json"
else:
    dir = sys.argv[1]

# collect all the JSON files
json_files = [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, '*.txt')
]

blacklist_files = [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'UI_Text.txt')
]

blacklist_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Name_Quest_AreaName.txt')
]

blacklist_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'ChipExplain_ActiveExplain.txt')
]

blacklist_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'ChipExplain_SupportExplain.txt')
]

bl = {"!", "＊", "†", "-", "士", "1", "2", "3", "4", "5"}


def pairr(j=None, t=None):
    if t is None:
        t = ""
    s = 0
    e = -1
    lj = len(j)
    if lj > 1:
        while s < (lj - 1) and j[s] in bl:
            s = s + 1
        yield s
        while e <= -(lj - 1) and j[e] in bl:
            e = e - 1
        yield e
    else:
        yield None
        yield None

    s = 0
    e = -1
    lt = len(t)
    if lt > 1:
        while s <= (lt - 1) and t[s] in bl:
            s = s + 1
        yield s
        while e <= -(lt - 1) and t[e] in bl:
            e = e - 1
        yield e
    else:
        yield None
        yield None


def normalizet(nk='NFKC', w=None):
    g = list()
    for t in w:
        tn = unicodedata.normalize(nk, t)
        trans = tn.maketrans(quick)
        g.append(tn.translate(trans))
    return g


for filename in json_files:
    update = False
    nk = 'NFKC'
    if filename in blacklist_files:
        nk = 'NFC'
    with codecs.open(filename, mode='r', encoding='utf-8') as json_file:
        djson = json.load(json_file, object_pairs_hook=OrderedDict)
        for entry in djson:
            for data in entry:
                if data.startswith('tr_'):
                    tl = data
                    jl = tl.replace("tr_", "jp_")
                    t = entry[tl]
                    if jl not in entry:
                        # We don't have JP explanations for titles, so don't report it
                        if filename.endswith("Title_All.txt") and jl == "jp_explain": continue
                        print("Missing {} in {}".format(jl, filename))
                        print(json.dumps(entry, ensure_ascii=False, indent="\t"))
                        continue
                    j = entry[jl]
                    if t == j:
                        continue
                    if t is None:
                        continue
                    if t == "":
                        continue
                    if type(j) is str:
                        w = {t}
                    else:
                        w = t
                    n = normalizet(nk, w)
                    if type(j) is str:
                        if n[0] == t:
                            continue
                    elif n == t:
                        continue
                    update = True
                    if len(n) == 1:
                        entry[tl] = n[0]
                    else:
                        entry[tl] = n

    if (update):
        counterr += 1
        print("Updating {}".format(filename))
        with codecs.open(filename, mode='w+', encoding='utf-8') as json_file:
            json.dump(
                djson, json_file, ensure_ascii=False,
                indent="\t", sort_keys=False)
            json_file.write("\n")

if counterr > 0:
    sys.exit("Issues found")
