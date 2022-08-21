#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import codecs
import fnmatch
import json
import os
import re
import sys

# Error counter
counterr = 0

bufout = "000.0%\t0FILE"
invalid_json_files = []

# Need the json path
if len(sys.argv) < 2:
    dir = "json"
else:
    dir = sys.argv[1]

json_files = [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, '*.txt')
]

for files in json_files:
    with codecs.open(files, mode='r', encoding='utf-8') as json_file:
        try:
            countin = 0
            countout = 0
            djson = json.load(json_file)
            linenames = ["text", "name", "title", "explain", "explainShort", "explainLong", "patterns"]
            for rmid in djson:
                for checkname in linenames:
                    if checkname == "explainShort" and (files.find("ActiveExplain") or files.find("SupportExplain")):
                        continue
                    # Exclude short descriptions for chip files (but not link skills)
                    
                    checkjp = "jp_" + checkname
                    if (
                        (checkjp in rmid)
                        and (re.match(r'^($)|(-)|(－)|(---)|(仮設定)|(仮テキスト)|(未使用)|(オミットアイテム)|(￥)|(\＊+$)|(＊￥)|(＊\\)|(ef_)|(bg_)|(wh_)|(ENT_)|(？？？.)', str(rmid[checkjp])) is None)
                        # Filter out dummy strings
                        and (re.match(r'^[a-zA-Z0-9 \＊\-\'\"\&\:\,\.\!\(\)\{\}\<\>\#\=\⇒\/\\]+$', str(rmid[checkjp])) is None)
                        # Filter out live strings that don't need translating
                       ):

                        countin += 1
                        checktr = "tr_" + checkname

                        if((checktr in rmid) and (rmid[checktr] != "") and (rmid[checktr] != rmid[checkjp])):
                            countout += 1

            # print ("%s/%s" % (countin, countout))
            if (countin):
                countper = "{:06.2%}".format(float(countout) / float(countin))
                bufout += '\n{0}\t{1} ({2}/{3})'.format(countper, files, countout, countin)
            else:
                bufout += '\n{0}\t:{1}'.format("No translatable lines found ", files)
        except ValueError as e:
            print("%s: %s") % (files, e)
            invalid_json_files.append(files)

counterr += len(invalid_json_files)

if counterr > 0:
    sys.exit("=============\nJSON files with issues: %d" % counterr)
else:
    print(bufout)
