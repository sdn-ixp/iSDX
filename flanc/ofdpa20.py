#  Author:
#  Rick Porter (Applied Communication Sciences)

import logging

class OFDPA20():
    __shared_state = {}

    def __init__(self, config, origin):
        self.__dict__ = self.__shared_state # makes this a singleton

        self.logger = logging.getLogger('OFDPA20')

        self.config = config
        self.origin = origin

        self.known_l2_ifcs = set()       # set of port #'s
        self.known_l2_overwrites = {}    # mapping from src/dst overwrite string to unique ID
        self.l2_overwrite_uniq = 0
        self.known_l2_multicast = set()  # mapping from mcast tuple of port #'s to unique ID
        self.l2_multicast_uniq = 0

        self.vlan = 1                    # untagged inputs go on vlan 1

    def get_table_id(self):
        print "FDP get_table"
        return 60

    def make_instructions_and_group_mods(self, fm, datapath):
        print "FDP make_iagm"
        fwd_ports = []
        eth_src = None
        eth_dst = None
        group_mods = []

        for action, value in fm.actions.iteritems():
            if action == "fwd":
                for port in value:
                    if isinstance( port, int ) or port.isdigit():
                        fwd_ports.append(int(port))
                    else:
                        if port in self.config.dp_alias:
                            port = self.config.dp_alias[port]
                        fwd_ports.append(self.config.datapath_ports[self.rule_type][port])
            elif action == "set_eth_src":
                eth_src = value
            elif action == "set_eth_dst":
                eth_dst = value

        if fwd_ports:
            for port in fwd_ports:
                print "FDP making l2 ifc group"
                group_mods.append(self.make_l2_interface_group_mod(fm, port, datapath))
        else:
            self.logger.warning('No forward action, so match will result in drop')

        if eth_src or eth_dst:
            if len(fwd_ports) > 1:
                self.logger.error('Multicast not supported in combination with MAC overwrite - ignoring all but first port')
            group_mods.append(self.make_l2_overwrite_group_mod(fm, fwd_ports[0], datapath, eth_src,eth_dst))
            group_actions = [fm.parser.OFPActionGroup(group_id=self.l2_overwrite_group_id(eth_src,eth_dst))]
        elif len(fwd_ports) == 1:
            group_actions = [fm.parser.OFPActionGroup(group_id=self.l2_interface_group_id(fwd_ports[0]))]
        else:
            print "FDP HUH?"

        instructions = [fm.parser.OFPInstructionActions(self.config.ofproto.OFPIT_APPLY_ACTIONS, group_actions)]
        return (instructions, group_mods)

    def make_l2_interface_group_mod(self, fm, port, datapath):
        actions = [fm.parser.OFPActionOutput(port),
                   fm.parser.OFPActionPopVlan()]
        buckets = [fm.parser.OFPBucket(actions=actions)]
        return fm.parser.OFPGroupMod(datapath=datapath,
                                       command=self.config.ofproto.OFPGC_ADD,
                                       type_=self.config.ofproto.OFPGT_INDIRECT,
                                       group_id=self.l2_interface_group_id(port),
                                       buckets=buckets)

    def l2_interface_group_id(self, port):
        return (self.vlan << 16) + (port & 0xffff)

    def make_l2_overwrite_group_mod(self, fm, port, datapath, eth_src, eth_dst):
        actions = [fm.parser.OFPActionGroup(group_id=self.l2_interface_group_id(port))]
        actions.append(fm.parser.OFPActionSetField("eth_src=" + eth_src)) if eth_src
        actions.append(fm.parser.OFPActionSetField("eth_dst=" + eth_dst)) if eth_dst
        buckets = [fm.parser.OFPBucket(actions=actions)]
        return fm.parser.OFPGroupMod(datapath=datapath,
                                       command=self.config.ofproto.OFPGC_ADD,
                                       type_=self.config.ofproto.OFPGT_INDIRECT,
                                       group_id=self.l2_overwrite_group_id(eth_src, eth_dst),
                                       buckets=buckets)

    def l2_overwrite_group_id(self, eth_src, eth_dst):
        overwrite_key = ('' if eth_src else "eth_src: " + eth_src) + ('' if eth_dst else " eth_dst: " + eth_dst)
        if not overwrite_key in self.known_l2_overwrites:
            self.known_l2_overwrites[overwrite_key] = (1 << 28) | (self.l2_overwrite_uniq++ & 0xfffffff)
        return self.known_l2_overwrites[overwrite_key]
