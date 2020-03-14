#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

for line in sys.stdin:
    if ("versionName=" in line):
        print("Updated to PSo2es v" + line.replace("versionName=", "").strip())
