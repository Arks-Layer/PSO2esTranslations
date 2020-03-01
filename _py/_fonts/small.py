#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import __init__ as _fonts
from collections import OrderedDict
import json
import unicodedata

FS = dict()

_fonts.init(100)

for char in range(0x0, 0xFFFF):
    ucd = unicodedata.name("{}".format(chr(char)), "UNKNOWN")
    if ucd == "UNKNOWN":
        chard = "{} | {} | {}".format(0, ucd, char)
    else:
        chard = "{} | {} | {}".format(chr(char), ucd, hex(char))
    FS[chard] = _fonts.textlength("★" + chr(char) + "★")-2

FSk = OrderedDict(sorted(FS.items(), key=lambda t: t[0]))
FSs = OrderedDict(sorted(FSk.items(), key=lambda t: t[1]))

print(json.dumps(FSs, ensure_ascii=False, indent="\t", sort_keys=False))
