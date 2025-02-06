#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import codecs
import fnmatch
import json
import os
import sys
import unicodedata

# count errros
counterr = 0
Forceso = False
bufout = "FILE: ID"
TRMap = dict()
JPMap = dict()
SPMap = dict()

# Need the json path
if len(sys.argv) < 2:
    dir = "json"
else:
    dir = sys.argv[1]

json_files = [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Item_*.txt')
]

json_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Explain_SkillRing.txt')
]

json_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Explain_System.txt')
]

json_files += [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, 'Items_Leftovers.txt')
]

for files in json_files:
    with codecs.open(files, mode='r', encoding='utf-8') as json_file:
        try:
            djson = json.load(json_file)
            for rmid in djson:
                if (("tr_text" in rmid) and (rmid["tr_text"] != "")):
                    t = rmid["tr_text"]
                    tl = t.lower()
                    if "jp_text" in rmid:
                        j = rmid["jp_text"]
                    else:
                        j = ""
                        print(rmid)
                        counterr += 1
                    jl = j.lower()
                    if "assign" in rmid:
                        a = rmid["assign"]
                    else:
                        a = 0

                    nt = unicodedata.normalize('NFKC', tl.replace(" ", "＊").replace("★", ""))
                    nj = unicodedata.normalize('NFKC', jl.replace(" ", "＊").replace("★", ""))

                    if jl not in JPMap:
                        JPMap[jl] = tl
                    elif JPMap[jl] != tl:
                        bufout += ("\nJP: {}:{} '{}' wants the mapping of i'{}' but already got i'{}'".format(
                            os.path.splitext(os.path.basename(files))[0],
                            a, j, tl, JPMap[jl]))
                        counterr += 1

                    if t not in TRMap:
                        TRMap[t] = jl
                    elif TRMap[t] != jl:
                        bufout += ("\nEN: {}:{} '{}' and '{}' both wants the mapping of '{}':".format(
                            os.path.splitext(os.path.basename(files))[0],
                            a, j, TRMap[t], t))
                        jsl = unicodedata.normalize('NFKC', j).rstrip().lower()
                        osl = unicodedata.normalize('NFKC', TRMap[t]).rstrip().lower()
                        if (jsl == osl):
                            bufout += "\n\tBut they are the same in our eyes"
                            Forceso = True
                        else:
                            counterr += 1

                    if "Explain_Actor_MagAuto.txt" in files:
                        continue

                    if jl == "ショウタイム":
                        continue

                    if nt not in SPMap:
                        SPMap[nt] = nj
                    elif SPMap[nt] != nj:
                        bufout += ("\nSP: {}:{} '{}' wants the mapping of i'{}' but already got i'{}'".format(
                            os.path.splitext(os.path.basename(files))[0],
                            a, j, tl, SPMap[nt]))
                        counterr += 1

                    if nj not in SPMap:
                        SPMap[nj] = nt
                    elif SPMap[nj] != nt:
                        bufout += ("\nSP: {}:{} '{}' wants the mapping of i'{}' but already got i'{}'".format(
                            os.path.splitext(os.path.basename(files))[0],
                            a, j, tl, SPMap[nt]))
                        counterr += 1

        except ValueError as e:
            counterr += 1
            print("%s: %s") % (files, e)

if counterr > 0:
    sys.exit(bufout)
elif Forceso or counterr < 0:
    print(bufout)
