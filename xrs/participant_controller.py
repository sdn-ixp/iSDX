#  Author:
#  Arpit Gupta (Princeton)

import json


class ParticipantController():
    def __init__(self, id):
        # participant id
        self.id = id
        
        self.port_2_participant = {}
        self.participant_2_port = {}
        self.portip_2_participant = {}
        self.participant_2_portip = {}
        self.portmac_2_participant = {}
        self.participant_2_portmac = {}
        self.asn_2_participant = {}
        self.participant_2_asn = {}
        self.supersets = []

        # VNHs related params
        self.num_VNHs_in_use = 0
        self.VNH_2_prefix = {}
        self.prefix_2_VNH = {}

        # Superset related params
        self.superset_threshold = 10
        self.max_superset_size = 30
        self.best_path_size = 12
        self.VMAC_size = 48
        self.VNHs = IPNetwork('172.0.1.1/24')

        # Communication with the Reference Monitor
        self.rest_api_url = 'http://localhost:8080/asdx/supersets'

        # Event Handler Module
        self.listener_eh = None
        self.set_receiver_events()

    def set_receiver_events(self):
        '''Start the listener socket for network events'''
        self.listener_qs = Listener(('localhost', port), authkey=None)
        ps_thread = Thread(target=self.start_eh)
        ps_thread.daemon = True
        ps_thread.start()

    def start_eh(self):
        ''' Socket listener for network events '''
        print "Event Handler started for", self.id
        while True:
            conn_qs = self.listener_qs.accept()
            tmp = conn.recv()
            data = json.loads(tmp)
            # TODO: Make sure that this receiver can process incoming network
            # events in parallel
            reply = process_event(data)
            conn_qs.send(tmp)
            conn_qs.close()

    def process_event(self, data):
        reply = ''
        if 'bgp' in data:
            route = data['bgp']
            self.process_bgp_route(route)

        return reply

    def process_bgp_route(self, route):
        reply = ''


        return reply
