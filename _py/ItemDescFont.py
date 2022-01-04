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

linelimit = 17.7


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
    f = os.path.splitext(os.path.basename(filename))[0]
    with codecs.open(filename, mode='r', encoding='utf-8') as json_file:
        djson = json.load(json_file)
        update = False
        for entry in djson:
            tt = entry["tr_text"]
            jt = entry["jp_text"]
            te = entry["tr_explain"]
            je = entry["jp_explain"]
            if tt == "":
                t = jt
            else:
                t = tt
            if te == "" or je == te:
                continue
            ce = remove_html_markup(te)
            fc = "{}:{}:{}".format(f, t, ce)
            FS[fc] = _fonts.textlength(ce)
            if (FS[fc] >= linelimit):
                ww = word_wrap(te, linelimit)
                FS[fc] = 0
                ce = remove_html_markup(ww)
                fc = "{}:{}:{}".format(f, t, ce)
                FS[fc] = _fonts.textlength(ce)
                entry["tr_explain"] = ww
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
        for f in fnmatch.filter(files, 'Explain_Actor_Mag*.txt')
    ]

    items_files += [
        os.path.join(dirpath, f)
        for dirpath, dirnames, files in os.walk(dir)
        for f in fnmatch.filter(files, 'Explain_Actor_StackDeviceSAA.txt')
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
            erra = 0
            try:
                erra += check(f)
            except Exception as ex:
                print("Error in {}: {}".format(f, ex))
    else:
        p = mp.Pool(mp.cpu_count())
        erra = p.map(check, items_files)
        p.close()
        p.join()
        counterr = max(erra)

    FSk = OrderedDict(sorted(FS.items(), key=lambda t: t[0]))
    FSs = OrderedDict(sorted(FSk.items(), key=lambda t: t[1]))

    if len(sys.argv) == 3:
        print(json.dumps(FSs, ensure_ascii=False, indent="\t", sort_keys=False))
    else:  # JP MAX: 42.73
        FSEP = OrderedDict((key, value) for key, value in FSs.items() if (value > linelimit))
        for e, s in FSEP.items():  # MAX: 32
            t = e.replace("\n", "\\n")
            print("Item Desc '{}' is too long: {}".format(t, s))

    # Disable error
    # counterr = -counterr

    if counterr > 0:
        sys.exit("Issues found")
