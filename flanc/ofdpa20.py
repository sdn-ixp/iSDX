#  Author:
#  Rick Porter (Applied Communication Sciences)

import logging

class OFDPA20():
    __shared_state = {}

    def __init__(self, config):
        self.__dict__ = self.__shared_state # makes this a singleton
        
        if hasattr(self,'config'):
            # shared instance already initialized
            return

        self.config = config

        self.logger = logging.getLogger('OFDPA20')

        self.vlan = 1                    # untagged inputs go on vlan 1

        self.l2_rewrite_to_gid = {}    # mapping from src/dst rewrite string to unique ID
        self.l2_rewrite_uniq = 0

        self.l2_multicast_to_gid = {}  # mapping from mcast tuple of port #'s to unique ID
        self.l2_multicast_uniq = 0

        self.gid_to_group_mod = {}
        self.installed_group_mods = set()

    def get_table_id(self):
        return 60

    def make_instructions_and_group_mods(self, fm, datapath):
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
                        fwd_ports.append(self.config.datapath_ports[fm.rule_type][port])
            elif action == "set_eth_src":
                eth_src = value
            elif action == "set_eth_dst":
                eth_dst = value
            else:
                self.logger.error('Unhandled action: ' + action)

        if fwd_ports:
            for port in fwd_ports:
                self.logger.debug("making l2 ifc group")
                group_mods.append(self.make_l2_interface_group_mod(fm, port, datapath))
        else:
            self.logger.warning('No forward action, so match will result in drop')

        if eth_src or eth_dst:
            if len(fwd_ports) > 1:
                self.logger.error('Multicast not supported in combination with MAC rewrite - ignoring all but first port')
            group_mods.append(self.make_l2_rewrite_group_mod(fm, fwd_ports[0], datapath, eth_src,eth_dst))
            group_actions = [fm.parser.OFPActionGroup(group_id=self.l2_rewrite_group_id(eth_src,eth_dst))]
        elif len(fwd_ports) == 1:
            group_actions = [fm.parser.OFPActionGroup(group_id=self.l2_interface_group_id(fwd_ports[0]))]
        elif len(fwd_ports) > 1:
            group_mods.append(self.make_l2_multicast_group_mod(fm, fwd_ports, datapath))
            group_actions = [fm.parser.OFPActionGroup(group_id=self.l2_multicast_group_id(fwd_ports))]
        else:
            self.logger.error("Unreachable code (I thought)!")

        instructions = [fm.parser.OFPInstructionActions(self.config.ofproto.OFPIT_APPLY_ACTIONS, group_actions)]
        return (instructions, group_mods)

    def make_group_mod(self, fm, datapath, gid, actions):
        if gid in self.gid_to_group_mod:
            # only ever create one GroupMod object for a gid
            return self.gid_to_group_mod[gid]
        buckets = [fm.parser.OFPBucket(actions=actions)]
        group_mod = fm.parser.OFPGroupMod(datapath=datapath,
                                       command=self.config.ofproto.OFPGC_ADD,
                                       type_=self.config.ofproto.OFPGT_INDIRECT,
                                       group_id=gid,
                                       buckets=buckets)
        self.gid_to_group_mod[gid] = group_mod
        return group_mod

    # L2 Interface Group stuff
    def make_l2_interface_group_mod(self, fm, port, datapath):
        actions = [fm.parser.OFPActionOutput(port),
                   fm.parser.OFPActionPopVlan()]
        return self.make_group_mod(fm, datapath, self.l2_interface_group_id(port), actions)

    def l2_interface_group_id(self, port):
        return (self.vlan << 16) + (port & 0xffff)

    # L2 Multicast Group stuff
    def make_l2_multicast_group_mod(self, fm, ports, datapath):
        actions = []
        for port in ports:
            actions.append(fm.parser.OFPActionGroup(group_id=self.l2_interface_group_id(port)))
        return self.make_group_mod(fm, datapath, self.l2_multicast_group_id(ports), actions)

    def l2_multicast_group_id(self, ports):
        mcast_key = tuple(sorted(ports))
        if not mcast_key in self.l2_multicast_to_gid:
            self.l2_multicast_to_gid[mcast_key] = 0x30000000 | (self.vlan << 16) | (self.l2_multicast_uniq & 0xffff)
            self.l2_multicast_uniq += 1
        return self.l2_multicast_to_gid[mcast_key]

    # L2 Rewrite Group stuff
    def make_l2_rewrite_group_mod(self, fm, port, datapath, eth_src, eth_dst):
        actions = [fm.parser.OFPActionGroup(group_id=self.l2_interface_group_id(port))]
        if eth_src:
            actions.append(fm.parser.OFPActionSetField(eth_src=eth_src))
        if eth_dst:
            actions.append(fm.parser.OFPActionSetField(eth_dst=eth_dst))
        return self.make_group_mod(fm, datapath, self.l2_rewrite_group_id(eth_src, eth_dst), actions)

    def l2_rewrite_group_id(self, eth_src, eth_dst):
        rewrite_key = ('' if not eth_src else "eth_src: " + eth_src) + ('' if not eth_dst else " eth_dst: " + eth_dst)
        if not rewrite_key in self.l2_rewrite_to_gid:
            self.l2_rewrite_to_gid[rewrite_key] = (1 << 28) | (self.l2_rewrite_uniq & 0xffff)
            self.l2_rewrite_uniq += 1
        return self.l2_rewrite_to_gid[rewrite_key]


    def is_group_mod_installed_in_switch(self, group_mod):
        return group_mod in self.installed_group_mods

    def mark_group_mod_as_installed(self, group_mod):
        self.logger.info('Group mod installed ' + str(group_mod))
        self.installed_group_mods.add(group_mod)
