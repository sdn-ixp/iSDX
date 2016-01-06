#!/usr/bin/python

'''
Send a single message at INFO level to log server.
'''

import argparse
import sys
import util.log

logger = util.log.getLogger('NOTE')
logger.info(' '.join(sys.argv[1:]))
