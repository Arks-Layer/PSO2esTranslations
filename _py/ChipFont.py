#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import _fonts
import codecs
from collections import OrderedDict
import fnmatch
import json
import os
import sys

# Error counter
counterr = 0

# Need the json path
if len(sys.argv) < 2:
    dir = "json"
else:
    dir = sys.argv[1]

FS = dict()

chip_files = [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Name_Chip_*.txt')
]

wpn_files = [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_Weapon_*.txt')
]

WPN = dict()

if len(sys.argv) == 3 and sys.argv[2] != "0":
    _fonts.init(int(sys.argv[2]))
else:
    _fonts.init()

for files in chip_files:
    with codecs.open(files, mode='r', encoding='utf-8') as json_file:
        djson = json.load(json_file)
        for entry in djson:
            t = entry["tr_text"]
            j = entry["jp_text"]
            if j == "" or j == "-":
                continue
            if j not in FS and False:
                FS[j] = _fonts.textlength(j)
            if t == "" or j == t:
                continue
            if t in FS:
                continue
            FS[t] = _fonts.textlength(t)

for files in wpn_files:
    with codecs.open(files, mode='r', encoding='utf-8') as json_file:
        djson = json.load(json_file)
        for entry in djson:
            t = entry["tr_text"]
            j = entry["jp_text"]
            if j == "" or j == "-":
                continue
            if False:
                WPN.update({j: False})
            if (t == "" or j == t) and t not in WPN:
                continue
            WPN.update({t: True})

FSk = OrderedDict(sorted(FS.items(), key=lambda t: t[0]))
FSs = OrderedDict(sorted(FSk.items(), key=lambda t: t[1]))

FSN = OrderedDict((key, value) for key, value in FSs.items() if key not in WPN)
FSW = OrderedDict((key, value) for key, value in FSs.items() if key in WPN)

FSL = OrderedDict()
FSL.update(FSN)  # Non-Weaponoid
FSL.update(FSW)  # Weaponoid

FSNER = OrderedDict((key, value) for key, value in FSN.items() if value >= 31.58)
FSWER = OrderedDict((key, value) for key, value in FSW.items() if value >= 19.61)

FSER = OrderedDict()

FSER.update(FSNER)  # Bigger then 60 first
FSER.update(FSWER)  # Bigger the 32 but less then 60 and in the weapon list

if len(sys.argv) == 3:
    print(json.dumps(FSL, ensure_ascii=False, indent="\t", sort_keys=False))
else:
    for e, s in FSER.items():
        counterr += 1
        print("Chip Name '{}' is too long: {}".format(e, s))

if counterr > 0:
    sys.exit("Issues found")
