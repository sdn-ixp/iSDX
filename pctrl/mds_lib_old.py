#############################################
# MDS Algorithm                             #
# author: Arpit Gupta (glex.qsd@gmail.com)  #
#############################################
import os
import sys
import time
from multiprocessing import Process, Queue
import multiprocessing as mp
import cProfile
from math import *
multiprocess = True

debug = False


def get_pset(plist):
    pset = []
    for elem in plist:
        pset.append(frozenset(elem))
    return set(pset)


def get_pdict(part_2_prefix):
    temp = set()
    for part in part_2_prefix:
        for plist in part_2_prefix[part]:
            if len(plist) > 1:
                temp = temp.union(set(plist))
                if (debug):
                    print "plist: ", plist
    return dict.fromkeys(list(temp), '')


def getMDS(part_2_prefix):
    MDS_out = []
    for participant in part_2_prefix:
        plist = part_2_prefix[participant]
        for elem in plist:
            MDS_out.append(frozenset(elem))
    MDS_out = set(MDS_out)
    MDS = []
    for elem in MDS_out:
        MDS.append(list(elem))
    print 'MDS_out: ', MDS
    return MDS


def divide_part2prefixes(plist, part_2_prefix):
    tmp = {}
    for elem in plist:
        tmp[elem] = part_2_prefix[elem]
    return tmp


def decompose_set(tdict, part_2_prefix_updated, tempdict_bk):
    # print "tdict: %s" % (tdict)
    pmap = []
    for key in tdict:
        for lst in tdict[key]:
            pmap.append(set(lst))
    # TODO: Use caching for this operation, possible benefits here
    min_set = set.intersection(*pmap)
    if (debug):
        print pmap
        print "min_set: ", min_set
    if len(min_set) > 0:
        for key in tdict:
            tlist = [min_set]
            for lst in tdict[key]:
                temp = (set(lst).difference(min_set))
                if len(temp) > 0:
                    tlist.append(temp)
            tdict[key] = tlist
            part_2_prefix_updated[key] += (tlist)
            for elem in tempdict_bk[key]:
                part_2_prefix_updated[key].remove(elem)
    return tdict


def decompose_simpler_multi(part_2_prefix, q=None):
    part_2_prefix_updated = part_2_prefix
    pdict = get_pdict(part_2_prefix_updated)
    # debug=True
    if (debug):
        if (debug):
            print "pdict: ", pdict
    for key in pdict:
        if (debug):
            print key
        tempdict = {}
        tempdict_bk = {}
        for part in part_2_prefix_updated:
            # tempdict[part]=[]
            tlist = []
            for temp in part_2_prefix_updated[part]:
                if key in temp:
                    tlist.append(temp)
            if len(tlist) > 0:
                tempdict[part] = tlist
                tempdict_bk[part] = tlist
        if (debug):
            print len(tempdict_bk), tempdict
        if (len(tempdict) == 1 and len(tempdict.values()[0]) == 1) == False:
            decompose_set(tempdict, part_2_prefix_updated, tempdict_bk)
        else:
            if (debug):
                if (debug):
                    print "avoided"
    MDS = []
    for part in part_2_prefix_updated:
        for temp in part_2_prefix_updated[part]:
            tset = set(temp)
            if tset not in MDS:
                MDS.append(tset)
    if (debug):
        if (debug):
            print "MDS: ", MDS
    if q is not None:
        q.put((part_2_prefix_updated, MDS))
        if (debug):
            print "Put operation completed", mp.current_process()
    else:
        return part_2_prefix_updated, MDS





def get_pdictReconstruct(part_2_prefix):
    temp = set()
    for part in part_2_prefix:
        for plist in part_2_prefix[part]:
            temp = temp.union(set(plist))
            if (debug):
                print "plist: ", plist
    return dict.fromkeys(list(temp), '')


def reconstruct(part_2_prefix, MDS, q=None):
    assert(len(part_2_prefix.keys()) == 1)
    part = part_2_prefix.keys()[0]
    part_2_prefix_updated = {}
    part_2_prefix_updated[part] = []
    pdict = get_pdictReconstruct(part_2_prefix)
    # if part==str(1): print "rc ",part, part_2_prefix
    completed = set()
    for pfx in pdict:
        if pfx not in completed:
            # print 'searching: ',pfx
            for psets in MDS.values()[0]:
                # print "analysing: ",psets
                if pfx in psets:
                    # if part==str(1): print "found ",pfx,psets
                    part_2_prefix_updated[part].append(psets)
                    # print part_2_prefix_updated

                    completed = completed.union(psets)
                    # if part==str(1): print completed

    return part_2_prefix_updated[part]


def decompose_multi(part_2_prefix, q=None, index=0):
    partList = part_2_prefix.keys()
    P = len(partList)
    Np = mp.cpu_count()
    if Np == 1:
        Np = 8  # dummy value
    
    if (debug): print "Started, len: ", P, part_2_prefix.keys()
    if P == 2:
        ndict = {}
        keys = part_2_prefix.keys()
        nkey = str(keys[0]) + str(keys[1])
        if (debug):
            print nkey
        x, MDS = decompose_simpler_multi(part_2_prefix)
        if (debug):
            print part_2_prefix
        ndict[nkey] = MDS
        if (debug):
            print "Completed, len: ", P, part_2_prefix.keys()
        if q is not None:
            q.put(ndict)
            if (debug):
                print "Put operation completed", mp.current_process()
        else:
            return ndict
    elif P == 1:

        ndict = {}
        # print part_2_prefix.keys()[0]
        x, MDS = decompose_simpler_multi(part_2_prefix)
        ndict[part_2_prefix.keys()[0]] = MDS
        if (debug):
            print "Completed, len: ", P, part_2_prefix.keys()
        if q is not None:
            q.put(ndict)
            if (debug):
                print "Put operation completed", mp.current_process()
        else:
            return ndict
    else:
        tmp = [divide_part2prefixes(partList[::2], part_2_prefix),
               divide_part2prefixes(partList[1::2], part_2_prefix)]
        process = []
        queue = []
        qout = []
        if (debug):
            print tmp[0], tmp[1]
        if (debug):
            print "index: ", index
        if index > 0 and index <= log(Np) / log(2):
            index += 1
            for i in range(2):
                queue.append(Queue())
                process.append(
                    Process(
                        target=decompose_multi,
                        args=(
                            tmp[i],
                            queue[i],
                            index)))
                process[i].start()
                if (debug):
                    print "Started: ", process[i]
            for i in range(2):
                if (debug):
                    print "Waiting for: ", process[i], i
                qout.append(queue[i].get())
                process[i].join()
                if (debug):
                    print "Joined: ", process[i], i
        else:
            if (debug):
                print "New process not spawned, index: ", index
            for p2p in tmp:
                qout.append(decompose_multi(p2p))

        MDS = decompose_multi(dict(qout[0].items() + qout[1].items()))
        if (debug):
            print "Completed, len: ", P, part_2_prefix.keys()
        if (debug):
            print MDS
        if q is not None:
            q.put(MDS)
            if (debug):
                print "Put operation completed", mp.current_process()
        else:
            return MDS


def MDS_multiprocess(part_2_prefix):
    '''
    Input: participant_2_prefixes: {participant: [prefix-group1, ...], ...}
    Output: part_2_prefix_updated: {participant:[set(prefix-group1), ...], ...}
    '''
    # Stage 1
    start = time.time()
    MDS = decompose_multi(part_2_prefix, index=1)
    print "# of MDS: ", len(MDS.values()[0])
    print "Completed MDS Computation in ", time.time() - start
    print "Now mapping the disjoint prefix groups to each participant ..."
    
    # Stage 2
    part_2_prefix_updated = {}
    for part in part_2_prefix:
        tmp = dict(({part:part_2_prefix[part]}).items())
        part_2_prefix_updated[part] = reconstruct(tmp, MDS)
    return part_2_prefix_updated, MDS.values()[0]


if __name__ == '__main__':
    part_2_prefix = {'A': [['p1', 'p2', 'p3']], 'C': [['p2', 'p3']], 'B': [
        ['p2', 'p3', 'p1'], ['p2', 'p3']], 'D': [['p2', 'p3', 'p1']]}
    print "Input:", part_2_prefix
    part_2_prefix, MDS = MDS_multiprocess(part_2_prefix)
    print "Output:", part_2_prefix, MDS
