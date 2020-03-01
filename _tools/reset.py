#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

# collect all the JSON files
json_files = [
    os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(dir)
    for f in fnmatch.filter(files, '*.txt')
]

for files in json_files:
    update = False
    f = os.path.splitext(os.path.basename(files))[0]
    with codecs.open(files, mode='r', encoding='utf-8') as json_file:
        print("Opening {}".format(files))
        djson = json.load(json_file, object_pairs_hook=OrderedDict)
        for entry in djson:
            for data in entry:
                if data.startswith('tr_'):
                    continue
                elif data.startswith('jp_'):
                    continue
                elif data == 'title_id':
                    continue
                elif data.endswith('_id'):
                    entry[data] = 0
                    update = True
                elif entry[data] != "":
                    entry[data] = None
                    update = True

    if (update):
        print("Updating {}".format(files))
        with codecs.open(files, mode='w+', encoding='utf-8') as json_file:
            json.dump(
                djson, json_file, ensure_ascii=False,
                indent="\t", sort_keys=False)
            json_file.write("\n")

if counterr > 0:
    sys.exit("Issues found")
