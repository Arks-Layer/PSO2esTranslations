#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import codecs
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

# collect all the JSON files
json_files = [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, '*.txt')
]

# build up blacklist
bl = dict()
for files in json_files:
    f = os.path.splitext(os.path.basename(files))[0]
    bl[f] = list()

#  Name_Actor_Enemy.txt
bl["Name_Actor_Enemy"] += ["DragonMagmaEx"]
#  UI_Server.txt
bl["UI_Server"] += ["313_t", "400_t", "221_t"]
bl["UI_Server"] += ["313_b", "400_b", "221_b"]
#  Name_Chip_ActiveName.txt
bl["Name_Chip_ActiveName"] += ["72020"]
# ChipExplain_ActiveExplain.txt
bl["ChipExplain_ActiveExplain"] += ["72020"]
#  Name_UICharMake_AccessoryName.txt
bl["Name_UICharMake_AccessoryName"] += ["No06421"]
bl["Name_UICharMake_AccessoryName"] += ["No14429"]
bl["Name_UICharMake_AccessoryName"] += ["No00090"]

for files in json_files:
    with codecs.open(files, mode='r', encoding='utf-8') as json_file:
        djson = json.load(json_file)
        assigns = dict()
        f = os.path.splitext(os.path.basename(files))[0]
        for entry in djson:
            if "assign" not in entry:
                continue
            if "text" not in entry:
                continue
            a = entry["assign"]
            if a in bl[f]:
                continue
            if "tr_text" in entry:
                t = entry["tr_text"]
                if t == "":
                    t = entry["jp_text"]
            elif "tr_explainShort" in entry:
                t = entry["tr_explainShort"]
                if t == "":
                    t = entry["jp_explainShort"]
            else:
                t = entry["text"]
            if a in assigns:
                print("{}: {}:{}/{}".format(
                    files,
                    a,
                    t,
                    assigns[a]
                ))
                counterr += 1
            else:
                assigns[a] = t

if counterr > 0:
    sys.exit("Issues found")
