import httplib
import json
from webob import Response

from ryu.app.wsgi import ControllerBase, route


# REST API for aSDX configuration
#
# change supersets
# POST /asdx/supersets
#
#  request body format:
#    {"type": "update/new",
#     "changes": [
#            {"participant": 81, "superset_id": 1, "index": 2},
#            {"participant": 34, "superset_id": 3, "index": 13},
#            ...]
#    }
#

url = '/asdx/supersets'

class aSDXController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(aSDXController, self).__init__(req, link, data, **config)
        self.asdx = data
        
    @route('asdx', url, methods=['POST'])
    def supersets_changed(self, req, **kwargs):
        try:
            update = json.loads(req.body)
        except SyntaxError:
            return Response(status=400)

        msgs = self.asdx.supersets_changed(update)
        
        body = json.dumps(msgs)
        return Response(content_type='application/json', body=body)