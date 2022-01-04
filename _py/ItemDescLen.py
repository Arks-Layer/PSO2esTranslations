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

FS3 = dict()
FS4 = dict()
FS5 = dict()

explain_files = [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_*.txt')
]

explain_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Explain_Actor_*.txt')
]

explain_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Explain_SkillRing.txt')
]

explain_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Explain_System.txt')
]
# -------------------------------------------------
explain4_files = [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Items_Leftovers.txt')
]

explain4_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_BaseWear_*.txt')
]

explain4_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_QuestTrigger.txt')
]

explain4_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_Stack_BodyPaint.txt')
]

explain4_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_Stack_GachaTradePass.txt')
]

explain4_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_Stack_Gat*.txt')
]

explain4_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_Stack_ItemBag.txt')
]

explain4_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_Stack_Music.txt')
]

explain4_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_Stack_PaidPass.txt')
]

explain4_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_Stack_PaidTicket.txt')
]

explain4_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_Stack_Roomgoods.txt')
]

explain4_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_Stack_Sticker.txt')
]

explain4_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_AvatarWPN_*.txt')
]

explain4_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_Stack_Orderitem.txt')
]

explain5_files = [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_Stack_Ring?.txt')
]

explain5_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_Stack_GatBoost.txt')
]

explainN_files = explain5_files + explain4_files

explain3_files = [x for x in explain_files if x not in explain4_files and x not in explain5_files]
explain4_files = [x for x in explain4_files if x not in explain5_files]

for files in explain3_files:
    f = os.path.splitext(os.path.basename(files))[0]
    with codecs.open(files, mode='r', encoding='utf-8') as json_file:
        djson = json.load(json_file)
        for entry in djson:
            if (entry["tr_text"] != ""):
                t = entry["tr_text"]
            else:
                t = entry["jp_text"]
            ft = u"{}:{}".format(f, t)
            if ft in FS3:
                print(ft)
            FS3[ft] = len(entry["tr_explain"].rstrip().split('\n<yellow>')[0].split('\n'))

FS3k = OrderedDict(sorted(FS3.items(), key=lambda t: t[0]))
FS3s = OrderedDict(sorted(FS3k.items(), key=lambda t: t[1]))
FS3WP = OrderedDict((key, value) for key, value in FS3s.items() if value > 3)

for files in explain4_files:
    f = os.path.splitext(os.path.basename(files))[0]
    with codecs.open(files, mode='r', encoding='utf-8') as json_file:
        djson = json.load(json_file)
        for entry in djson:
            if (entry["tr_text"] != ""):
                t = entry["tr_text"]
                
            else:
                t = entry["jp_text"]
            ft = u"{}:{}".format(f, t)
            if ft in FS4:
                print(ft)
            FS4[ft] = len(entry["tr_explain"].rstrip().split('\n'))

FS4k = OrderedDict(sorted(FS4.items(), key=lambda t: t[0]))
FS4s = OrderedDict(sorted(FS4k.items(), key=lambda t: t[1]))
FS4WP = OrderedDict((key, value) for key, value in FS4s.items() if value > 4)

for files in explain5_files:
    f = os.path.splitext(os.path.basename(files))[0]
    with codecs.open(files, mode='r', encoding='utf-8') as json_file:
        djson = json.load(json_file)
        for entry in djson:
            if (entry["tr_text"] != ""):
                t = entry["tr_text"]
            else:
                t = entry["jp_text"]
            ft = "{}:{}".format(f, t)
            if ft in FS5:
                print(ft)
            FS5[ft] = len(entry["tr_explain"].rstrip().split('\n'))

FS5k = OrderedDict(sorted(FS5.items(), key=lambda t: t[0]))
FS5s = OrderedDict(sorted(FS5k.items(), key=lambda t: t[1]))
FS5WP = OrderedDict((key, value) for key, value in FS5s.items() if value > 5)

FSER = OrderedDict()

FSER.update(FS4WP)
FSER.update(FS3WP)

for e, s in FSER.items():
    counterr += 1
    try:
        print("Item Desc '{}' is too big: {}".format(e, s))
    except UnicodeEncodeError:
        print(u"Item Desc '{}' is too big: {}".format(e, s))


# Do not fail
counterr = -counterr

if counterr > 0:
    sys.exit("Issues found")
