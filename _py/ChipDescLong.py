#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import _fonts
import codecs
from collections import OrderedDict
import fnmatch
import json
import os
import sys

linelimit = 24.67

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
    for f in fnmatch.filter(files, 'ChipExplain_*.txt')
]

if len(sys.argv) == 3 and sys.argv[2] != "0":
    _fonts.init(int(sys.argv[2]))
else:
    _fonts.init()


def word_wrap(string, width=00.00):
    words = string.replace(" \n", " ").replace("\n", " ").split(" ")
    newstrings = []
    current = ""
    wordi = 0

    while True:
        current = ""
        lastgood = ""

        if len(words) == wordi:
            break

        while len(words) > wordi:
            current = current

            if (current == ""):
                current += words[wordi]
            else:
                current += " " + words[wordi]

            if (_fonts.textlength(remove_html_markup(current)) >= width):
                break

            lastgood = current
            wordi += 1

        if (lastgood == "" and len(words) > wordi):
            lastgood = words[wordi]
            wordi += 1

        if (lastgood != ""):
            newstrings.append(lastgood)

    warped = "\n".join(newstrings)

    return warped


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


def check(filename):
    f = os.path.splitext(os.path.basename(files))[0]
    with codecs.open(files, mode='r', encoding='utf-8') as json_file:
        djson = json.load(json_file)
        update = False
        for entry in djson:
            te = entry["tr_explainLong"]
            je = entry["jp_explainLong"]
            an = entry["assign"]
            if te == "" or je.replace("\r\n", "\n") == te:
                continue
            c = remove_html_markup(te)
            if te in FS:
                continue
            ce = remove_html_markup(te)
            fc = "{}:{}:{}".format(f, an, ce)
            FS[fc] = _fonts.textlength(c)
            if (FS[fc] >= linelimit):
                ww = word_wrap(te, linelimit)
                FS[fc] = 0
                ce = remove_html_markup(ww)
                fc = "{}:{}:{}".format(f, an, ce)
                FS[fc] = _fonts.textlength(ce)
                entry["tr_explainLong"] = ww
                update = True

        if (update):
            print("Updating {}".format(filename))
            with codecs.open(filename, mode='w+', encoding='utf-8') as json_file:
                json.dump(
                    djson, json_file, ensure_ascii=False,
                    indent="\t", sort_keys=False)
                json_file.write("\n")
            return 1
    return 0


for files in chip_files:
    counterr += check(files)

FSk = OrderedDict(sorted(FS.items(), key=lambda t: t[0]))
FSs = OrderedDict(sorted(FSk.items(), key=lambda t: t[1]))

if len(sys.argv) == 3:
    print(json.dumps(FSs, ensure_ascii=False, indent="\t", sort_keys=False))
else:  # JP MAX: 46.86
    FSEP = OrderedDict((key, value) for key, value in FSs.items() if value > linelimit)
    for e, s in FSEP.items():  # MAX: 42.5
        t = e.replace("\n", "\\n")
        counterr += 1
        print("Chip Long explain '{}' is too big: {}".format(t, s))

# counterr = -counterr

if counterr > 0:
    sys.exit("Issues found")
