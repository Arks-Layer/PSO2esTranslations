#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import _fonts
import codecs
from collections import OrderedDict
import fnmatch
import json
import multiprocessing as mp
import os
import platform
import sys


def remove_html_markup(s):
    tag = False
    quote = False
    out = ""

    for c in s:
            if c == '<' and not quote:
                tag = True
            elif c == '>' and not quote:
                tag = False
            elif (c == '"' or c == "'") and tag:
                quote = not quote
            elif not tag:
                out = out + c
    return out


def check(files):
    f = os.path.splitext(os.path.basename(files))[0]
    with codecs.open(files, mode='r', encoding='utf-8') as json_file:
        djson = json.load(json_file)
        for entry in djson:
            tt = entry["tr_text"]
            if tt == "":
                continue
            fc = "{}:{}".format(f, tt)
            FS[fc] = _fonts.textlength(tt)


if __name__ == '__main__':
    mp.freeze_support()
    # error counter
    counterr = 0

    # Need the json path
    if len(sys.argv) < 2:
        dir = "json"
    else:
        dir = sys.argv[1]

    manager = mp.Manager()
    FS = manager.dict()

    items_files = [
        os.path.join(dirpath, f)
        for dirpath, dirnames, files in os.walk(dir)
        for f in fnmatch.filter(files, 'Item_*.txt')
    ]

    items_files += [
        os.path.join(dirpath, f)
        for dirpath, dirnames, files in os.walk(dir)
        for f in fnmatch.filter(files, 'Explain_Actor_*.txt')
    ]

    items_files += [
        os.path.join(dirpath, f)
        for dirpath, dirnames, files in os.walk(dir)
        for f in fnmatch.filter(files, 'Explain_SkillRing.txt')
    ]

    items_files += [
        os.path.join(dirpath, f)
        for dirpath, dirnames, files in os.walk(dir)
        for f in fnmatch.filter(files, 'Explain_System.txt')
    ]

    items_files += [
        os.path.join(dirpath, f)
        for dirpath, dirnames, files in os.walk(dir)
        for f in fnmatch.filter(files, 'Items_Leftovers.txt')
    ]

    if len(sys.argv) == 3 and sys.argv[2] != "0":
        _fonts.init(int(sys.argv[2]))
    elif platform.system() == 'Windows':
        _fonts.init(1)
    else:
        _fonts.init()

    if platform.system() == 'Windows':
        for f in items_files:
            try:
                check(f)
            except Exception as ex:
                print("Error in {}: {}".format(f, ex))
    else:
        p = mp.Pool(mp.cpu_count())
        erra = p.map(check, items_files)
        p.close()
        p.join()

    FSk = OrderedDict(sorted(FS.items(), key=lambda t: t[0]))
    FSs = OrderedDict(sorted(FSk.items(), key=lambda t: t[1]))

    if len(sys.argv) == 3:
        print(json.dumps(FSs, ensure_ascii=False, indent="\t", sort_keys=False))
    else:  # JP MAX: 25.21
        FSEP = OrderedDict((key, value) for key, value in FSs.items() if value > 18)
        for e, s in FSEP.items():  # MAX: 27.34
                t = e.replace("\n", "\\n")
                counterr += 1
                print("Item Name '{}' is too long: {}".format(t, s))

    # Disable error
    # counterr = -counterr

    if counterr > 0:
        sys.exit("Issues found")
