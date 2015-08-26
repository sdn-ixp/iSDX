#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import httplib

import json
from webob import Response

from ryu.app.wsgi import ControllerBase, route


url = '/refmon/flowmod'

class FlowModReceiver(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(FlowModReceiver, self).__init__(req, link, data, **config)
        self.refmon = data

    @route('refmon', url, methods=['POST'])
    def supersets_changed(self, req, **kwargs):
        try:
            data = json.loads(req.body)
        except SyntaxError:
            return Response(status=400)

        msgs = self.refmon.process_flow_mods(data)

        body = json.dumps(msgs)
        return Response(content_type='application/json', body=body)
