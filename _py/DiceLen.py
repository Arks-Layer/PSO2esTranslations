#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

dice_files = [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Leisure_PhotonDice_SpeakText.txt')
]

for files in dice_files:
    with codecs.open(files, mode='r', encoding='utf-8') as json_file:
        djson = json.load(json_file)
        for entry in djson:
            te = entry["tr_patterns"]
            je = entry["jp_patterns"]
            for b in te:
                if (b == ""):
                    continue
                if (b not in FS):
                    continue
                FS[b] = len(b.rstrip().split('\n'))

FSk = OrderedDict(sorted(FS.items(), key=lambda t: t[0]))
FSs = OrderedDict(sorted(FSk.items(), key=lambda t: t[1]))

FSER = OrderedDict((key, value) for key, value in FSs.items() if value > 3)

if len(sys.argv) == 3:
    print(json.dumps(FSs, ensure_ascii=False, indent="\t", sort_keys=False))
else:  # JP MAX: 31.12
    for e, s in FSER.items():
        t = e.replace("\r\n", "\\r\\n")
        counterr += 1
        print("Dice SpeakText '{}' have too many lines: {}".format(t, s))

if counterr > 0:
    sys.exit("Issues found")
