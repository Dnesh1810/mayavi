#!/usr/bin/env python
import os
import sys

path = os.environ.get(
    "mapreduce_map_input_file",
    os.environ.get("map_input_file", "unknown")
)
filename = os.path.basename(path)

for line in sys.stdin:
    sys.stdout.write("%s\t1\n" % filename)
