#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from PIL import ImageFont

fontS = None
fontR = None


def init(scale=4):
    global fontR
    global fontS
    size = 72
    size *= scale
    fontS = scale
    font = os.path.join(
        os.path.dirname(
            os.path.realpath(__file__)
        ),
        "DF-HeiSeiGothic-W7003.ttf"
    )
# "DF-SouGei-W7003.ttf"
# "DF-HeiSeiGothic-W7003.ttf"
    fontR = ImageFont.truetype(
        font=font,
        size=size
    )


def textlength(name=""):
    global fontR
    global fontS
    w = -1
    h = -1
    t = name.replace("<%br>", "\n").replace("<br>", "\n").replace("\\n", "\n").rstrip()
    for sl in t.splitlines():
        w, h = max(fontR.getsize(sl), (w, h))
    return w / (72 * fontS)
