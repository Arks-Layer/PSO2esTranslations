#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import _fonts
import codecs
from collections import OrderedDict
import fnmatch
import json
import os
import sys

# error counter
counterr = 0

# Need the json path
if len(sys.argv) < 2:
    dir = "json"
else:
    dir = sys.argv[1]

FS = dict()
FSl = dict()

story_files = [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Season*_Text.txt')
]

story_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'SideStoryEvent_Text.txt')
]

story_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'UI_Weaponoid_SideStoryOpen.txt')
]

if len(sys.argv) == 3 and sys.argv[2] != "0":
    _fonts.init(int(sys.argv[2]))
else:
    _fonts.init()

for files in story_files:
    with codecs.open(files, mode='r', encoding='utf-8') as json_file:
        djson = json.load(json_file)
        for entry in djson:
            for text in entry:
                if (text != "tr_buttons"):
                    continue
                for t in entry[text]:
                    if (t == ""):
                        continue
                    if t in FS:
                        continue
                    FS[t] = _fonts.textlength(t)
                    FSl[t] = os.path.basename(files)

FSk = OrderedDict(sorted(FS.items(), key=lambda t: t[0]))
FSs = OrderedDict(sorted(FSk.items(), key=lambda t: t[1]))

if len(sys.argv) == 3:
    print(json.dumps(FSs, ensure_ascii=False, indent="\t", sort_keys=False))
else:  # JP MAX: 34.24
    FSWP = OrderedDict((key, value) for key, value in FSs.items() if value > 25.26)
    for e, s in FSWP.items():  # TXT MAX: Center mess
        t = e.replace("\n", "br")
        if s > 64:
            counterr += 1
        print("{}'s Story Button '{}' is too long: {}".format(FSl[t], t, s))

if counterr > 0:
    sys.exit("Issues found")
