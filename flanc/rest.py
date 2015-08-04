#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import httplib

import json
from webob import Response

from ryu.app.wsgi import ControllerBase, route


# REST API for aSDX configuration
#
# send flow_mod
# POST /refmon/flow_mod
#
#  request body format:
#    {"auth_info": {
#            "participant": 1,
#            "key": "xyz"
#            }
#     "flow_mods": [
#            { "id": 1, 
#              "mod_type": "add/remove",
#              "rule_type": "inbound/outbound/main",
#              "match" : {
#                         "ipv4_src" : "192.168.1.1", 
#                         "ipv4_dst" : "192.168.1.2", 
#                         "tcp_src" : 80, 
#                         "tcp_dst" : 179,
#                         "udp_src" : 23,
#                         "udp_dst" : 22, 
#                        },
#              "action" : {"fwd": 1}
#            },
#            { "id": 2,
#              "mod_type": "add/remove",
#              "rule_type": "inbound/outbound/main",
#              "match" : {"tcp_dst" : 80},
#              "action" : {"fwd": 3}
#            }
#            ...]
#    }
#

url = '/refmon/flow_mod'

class RESTHandler(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(RESTHandler, self).__init__(req, link, data, **config)
        self.refmon = data
        
    @route('refmon', url, methods=['POST'])
    def supersets_changed(self, req, **kwargs):
        try:
            msg = json.loads(req.body)
        except SyntaxError:
            return Response(status=400)

        msgs = self.refmon.process_flow_mods(msg)
        
        body = json.dumps(msgs)
        return Response(content_type='application/json', body=body)
