#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import requests
import json
from netaddr import *

from bgp_interface import get_all_participants_advertising

LOG = False

#
### VNH ASSIGNMENT
#

def vnh_assignment(updates, xrs):
    for update in updates:
        if ('announce' in update):
            prefix = update['announce']['prefix']
            
            if (prefix not in xrs.prefix_2_VNH):
                # get next VNH and assign it the prefix
                xrs.num_VNHs_in_use += 1
                vnh = str(xrs.VNHs[xrs.num_VNHs_in_use])
                
                xrs.prefix_2_VNH[prefix] = vnh
                xrs.VNH_2_prefix[vnh] = prefix

#                
### VMAC BUILDER
#

def vmac(vnh, participant, xrs):

    vmac_bitstring = ""
    vmac_addr = ""
    
    if vnh in xrs.VNH_2_prefix:
        # get corresponding prefix
        prefix = xrs.VNH_2_prefix[vnh]
        # get set of participants advertising prefix
        basic_set = get_all_participants_advertising(prefix, xrs.participants)
        # get corresponding superset identifier
        superset_identifier = 0
        for i in range(0, len(xrs.supersets)):
            if ((set(xrs.supersets[i])).issuperset(basic_set)):
                superset_identifier = i
                break
                
        vmac_bitstring = '{num:0{width}b}'.format(num=superset_identifier, width=(xrs.VMAC_size-xrs.max_superset_size-xrs.best_path_size))
        
        # add one bit for each participant that is a member of the basic set and has a "link" to it
        set_bitstring = ""
        for temp_participant in xrs.supersets[superset_identifier]:
            if (temp_participant in basic_set and temp_participant in xrs.participants[participant].peers_out):
                set_bitstring += "1"
            else:
                set_bitstring += "0"
        if (len(set_bitstring) < xrs.max_superset_size):
            set_bitstring += '{num:0{width}b}'.format(num=0, width=(xrs.max_superset_size-len(set_bitstring)))
            
        vmac_bitstring += set_bitstring
        
        # add identifier of best path
        route = xrs.participants[participant].get_route('local',prefix)
        if route:
            best_participant = xrs.portip_2_participant[route['next_hop']]

            vmac_bitstring += '{num:0{width}b}'.format(num=best_participant, width=(xrs.best_path_size))

            # convert bitstring to hexstring and then to a mac address
            vmac_addr = '{num:0{width}x}'.format(num=int(vmac_bitstring,2), width=xrs.VMAC_size/4)
            vmac_addr = ':'.join([vmac_addr[i]+vmac_addr[i+1] for i in range(0,xrs.VMAC_size/4,2)])
            
            if LOG:
                print "VMAC-Mapping"
                print "Participant: "+str(participant)+", Prefix: "+str(prefix)+"Best Path: "+str(best_participant)
                print "Superset "+str(superset_identifier)+": "+str(xrs.supersets[superset_identifier])
                print "VMAC: "+str(vmac_addr)+", Bitstring: "+str(vmac_bitstring)
        
    return vmac_addr

#                
### VMAC BEST PATH
#
    
def vmac_best_path(participant_id, xrs):
        
    # add participant identifier
    vmac_bitstring = '{num:0{width}b}'.format(num=participant_id, width=(xrs.VMAC_size))

    # convert bitstring to hexstring and then to a mac address
    vmac_addr = '{num:0{width}x}'.format(num=int(vmac_bitstring,2), width=xrs.VMAC_size/4)
    vmac_addr = ':'.join([vmac_addr[i]+vmac_addr[i+1] for i in range(0,xrs.VMAC_size/4,2)])
            
    return vmac_addr
    
#                
### UPDATE SDX CONTROLLER
#
    
def update_sdx_controller(changes, url):
    payload = changes
    r = requests.post(url, data=json.dumps(payload))
    
    if LOG:
        if (r.status_code == requests.codes.ok):
            print "XRS->SDX: Superset Update Succeeded - "+str(r.status_code)
        else:
            print "XRS->SDX: Superset Update Failed - "+str(r.status_code)
    