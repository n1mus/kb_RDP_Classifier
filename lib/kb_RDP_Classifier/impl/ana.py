'''
Data structures
'''
import pandas as pd
import numpy as np

from . import app_file
from ..util.debug import dprint


ROOT_PATH = 'Root;'

class TaxTree: 
    '''
    For plotly sunburst with variable depth
    '''
    nodes = {}

    class Node:
        
        def __init__(self, path_l: list):
            self.name = path_l[-1]
            self.path_l = path_l
            self.path_s = ';'.join(path_l) + ';'
            self.count = 0
            self._num_leaf = 0 # number paths ending here

        @property
        def id(self):
            return self.path_s

        @property
        def parent_id(self):
            if self.path_s == ROOT_PATH: return ''
            return ';'.join(self.path_l[:-1]) + ';'

        @property
        def color_id(self):
            if len(self.path_l) <= 2:
                return self.name
            else:
                return self.path_l[2]
        
    @classmethod
    def build(cls) -> None:
        id2tax = app_file.get_fix_filtered_id2tax()
        id2tax = {
            id: ROOT_PATH + tax for id, tax in id2tax.items()
        }
        id2tax = {k: v for k, v in sorted(id2tax.items(), key=lambda item: item[1])} # sort dict by value so sunburst is alphabetical

        cls.nodes.clear()
        cls.num_records = len(id2tax) 

        for id, tax in id2tax.items():
            taxname_l = tax.split(';')[:-1]

            for i in range(len(taxname_l)):
                path_l = taxname_l[:i + 1]
                path_s = ';'.join(path_l) + ';'

                if path_s in cls.nodes:
                    node = cls.nodes[path_s]
                    node.count = node.count + 1
                else:
                    node = cls.Node(path_l)
                    cls.nodes[path_s] = node
                    node.count = node.count + 1

            node._num_leaf = node._num_leaf + 1

        cls._sanity_check()


    @classmethod
    def _sanity_check(cls) -> None:

        ## Sanity checks
        num_leaves = 0
        for path_s, node in cls.nodes.items():
            num_leaves = num_leaves + node._num_leaf

        root = cls.nodes[ROOT_PATH]

        assert num_leaves == root.count and root.count == cls.num_records, \
                '%d vs %d vs %d' % (num_leaves, root.count, cls.num_records)


    @classmethod
    def get_sunburst_lists(cls) -> tuple:

        names = [] # labels
        parent_ids = [] # parents
        counts = [] # values
        ids = [] # ids
        color_ids = [] # color_ids

        for path_s, node in cls.nodes.items():
            names.append(node.name)
            parent_ids.append(node.parent_id)
            counts.append(node.count)
            ids.append(node.id)
            color_ids.append(node.color_id)

        return names, parent_ids, counts, ids, color_ids


def get_cutoff_rank_counts():
    id2tax = app_file.get_fix_filtered_id2tax()

    ranks = ['root', 'domain', 'phylum', 'class', 'order', 'family', 'genus']

    counts = {}
    for i, rank in enumerate(ranks):
        counts[rank] = len([
            t for t in id2tax.values() if t.count(';') == i
        ])

    assert sum([ct for ct in counts.values()]) == len(id2tax)

    return counts


def get_rank2confs():
    df = app_file.get_fixRank()

    ranks = ['domain', 'phylum', 'class', 'order', 'family', 'genus']

    rank2confs = {}
    for rank in ranks:
        conf_l = df[rank + '_conf'].tolist()
        conf_l = [
            float(conf) for conf in conf_l if not (type(conf) is float and np.isnan(conf))
        ]
        rank2confs[rank] = conf_l

    return rank2confs
        

def hist_0_1_10(l):
    '''Use np to hist but with [s,e) instead of (s,e] by nudging edges ever so slightly back
    Rightmost max values nudged even more back so last bin catches them'''
    femto = 1e-15 # femto nudge bin edges back
    micro = 1e-6 # micro nudge rightmost max values back
    l = [e if e<1 else e-micro for e in l]
    h = np.histogram(l, range=[0-femto,1-femto], bins=10)[0]
    return h

