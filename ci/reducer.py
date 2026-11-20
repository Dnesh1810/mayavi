#!/usr/bin/env python
import sys

current = None
total = 0

for line in sys.stdin:
    filename, count = line.strip().split("\t", 1)
    if filename != current:
        if current is not None:
            sys.stdout.write("%s\t%d\n" % (current, total))
        current = filename
        total = 0
    total += int(count)

if current is not None:
    sys.stdout.write("%s\t%d\n" % (current, total))
