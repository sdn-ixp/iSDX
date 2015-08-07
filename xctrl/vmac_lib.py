#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

from netaddr import *
import math

#                
### VMAC AND VMAC MASK BUILDERS
#

class VMACBuilder(object):
    def __init__(self, config):
        self.vmac_size = config["VMAC Size"]
        self.next_hop_size = config["Next Hop Field"]
        self.port_size = config["Port Field"]
        self.custom_field_size = ["Participant Field"]

    # constructs a match VMAC for checking next-hop
    def next_hop_match(self, participant_name, inbound_bit = False):
        
        # add participant identifier
        vmac_bitstring = '{num:0{width}b}'.format(num=participant_name, width=(self.vmac_size))

        # set the 'inbound policy required' bit
        if inbound_bit:
            vmac_bitstring = '1' + vmac_bitstring[1:]

        # convert bitstring to hexstring and then to a mac address
        vmac_addr = '{num:0{width}x}'.format(num=int(vmac_bitstring,2), width=self.vmac_size/4)
        vmac_addr = ':'.join([vmac_addr[i]+vmac_addr[i+1] for i in range(0,self.vmac_size/4,2)])
            
        return vmac_addr

    # returns a mask on just participant bits
    def next_hop_mask(self, inbound_bit = False):
        part_bits_only = (1 << self.next_hop_size) - 1

        bitmask = self.next_hop_match(part_bits_only, inbound_bit)

        return bitmask


    # constructs stage-2 VMACs (for both matching and assignment)
    def part_port_match(self, participant_name, port_num, inbound_bit = False):
        part_bits = self.next_hop_size
        remainder = self.vmac_size - part_bits

        # padding and port identifier on the left
        vmac_bitstring_part1 = '{num:0{width}b}'.format(num=port_num, width=remainder)
        # participant identifier on the right
        vmac_bitstring_part2 = '{num:0{width}b}'.format(num=participant_name, width=part_bits)
        # combined
        vmac_bitstring = vmac_bitstring_part1 + vmac_bitstring_part2

        # set the 'inbound policy required' bit
        if inbound_bit:
            vmac_bitstring = '1' + vmac_bitstring[1:]

        # convert bitstring to hexstring and then to a mac address
        vmac_addr = '{num:0{width}x}'.format(num=int(vmac_bitstring,2), width=self.vmac_size/4)
        vmac_addr = ':'.join([vmac_addr[i]+vmac_addr[i+1] for i in range(0,self.vmac_size/4,2)])

        return vmac_addr


    # returns a mask on participant and port bits
    def part_port_mask(self, inbound_bit = False):
        part_port_size = self.next_hop_size + self.port_size
        part_port_bits = (1 << part_port_size) - 1

        bitmask = self.next_hop_match(part_port_bits, inbound_bit)
    
        return bitmask

    # looks like 100000000000000
    def only_first_bit(self):
        # return a match on participant 0 with inbound bit set to 1
        return self.next_hop_match(0, inbound_bit=True)
