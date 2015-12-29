#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import os
import sys
np = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if np not in sys.path:
    sys.path.append(np)
import pctrl.ss_lib as ss_lib
import pctrl.supersets as supersets

#
### VMAC AND VMAC MASK BUILDERS
#

class VMACBuilder(object):
    def __init__(self, logger, config):
        self.logger = logger

        self.ss_instance = supersets.SuperSets(self, config)


    # constructs a match VMAC for checking next-hop
    def next_hop_match(self, participant_name, inbound_bit = False):

        return ss_lib.vmac_next_hop_match(participant_name, self.ss_instance, inbound_bit)


    # returns a mask on just participant bits
    def next_hop_mask(self, inbound_bit = False):

        return ss_lib.vmac_next_hop_mask(self.ss_instance, inbound_bit)

    # constructs stage-2 VMACs (for both matching and assignment)
    def part_port_match(self, participant_name, port_num, inbound_bit = False):

        return ss_lib.vmac_part_port_match(participant_name, port_num,
                                        self.ss_instance, inbound_bit)


    # returns a mask on participant and port bits
    def part_port_mask(self, inbound_bit = False):

        return ss_lib.vmac_part_port_mask(self.ss_instance, inbound_bit)


    # looks like 100000000000000
    def only_first_bit(self):

        return ss_lib.vmac_only_first_bit(self.ss_instance)
