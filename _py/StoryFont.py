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
            t = entry["tr_text"]
            j = entry["jp_text"]
            if j.replace("\r\n", "\n") == t:
                t = ""
            if (t == ""):
                continue
            if (t in FS):
                continue
            FS[t] = _fonts.textlength(t)

FSk = OrderedDict(sorted(FS.items(), key=lambda t: t[0]))
FSs = OrderedDict(sorted(FSk.items(), key=lambda t: t[1]))

if len(sys.argv) == 3:
    print(json.dumps(FSs, ensure_ascii=False, indent="\t", sort_keys=False))
else:  # JP MAX: 37.53
    FSWP = OrderedDict((key, value) for key, value in FSs.items() if value > 24.75)
    for e, s in FSWP.items():  # TXT MAX: 45
        t = e.replace("\n", "br")
        counterr += 1
        print("Story Text '{}' is too long: {}".format(t, s))

if counterr > 0:
    sys.exit("Issues found")
