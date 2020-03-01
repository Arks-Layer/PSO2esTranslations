#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

for line in sys.stdin:
    if (line.strip() is not ""):
        print(line.replace("package:", "").rstrip())
