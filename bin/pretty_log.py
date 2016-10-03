#!/usr/bin/env python

# Script for pretty printing the SDXlog file.
# This will pretty print any json in the log that was formatted using the util.log.pformat() function
# (so long as the json string is at the end of the line).

import pprint
import json
import fileinput

for line in fileinput.input():
    s = line.rstrip("\r\n")
    i = s.find('{')
    if i == -1:
        print s
        continue
    # looks like it might be json
    try:
        # load it and pretty print it
        msg = json.loads(s[i:])
        print s[:i] + "\n" + pprint.pformat(msg)
    except:
        # it was't json after all.  Just print it.
        print s
