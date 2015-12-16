#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import json
import requests

class FlowModSender(object):
    def __init__(self, url):
        self.url = url

    def send(self, msg):
        payload = msg
        r = requests.post(self.url, data=json.dumps(payload))

        if (r.status_code == requests.codes.ok):
            print "FlowMod Succeeded - "+str(r.status_code)
        else:
            print "FlowMod Failed - "+str(r.status_code)
