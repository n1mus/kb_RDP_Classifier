'''
Data structures
'''
import pandas as pd
import numpy as np

from . import app_file


ROOT_RANK = 'root'
ROOT_NAME = 'Root'
RANKS = [ROOT_RANK, 'domain','phylum','class','order','family','genus']


class TaxTree: # this class can be removed and the module would suffice
    '''
    For plotly sunburst with variable depth
    '''
    nodes = {}

    class Node:
        
        def __init__(self, path_l: list):
            self.name = path_l[-1]
            self.path_l = path_l
            self.path_s = ';'.join(path_l)
            self.rank = RANKS[len(path_l) - 1]
            self.count = 0
            self.num_leaf = 0 # number paths ending here

        @property
        def id(self):
            return self.path_s

        @property
        def parent_id(self):
            return ';'.join(self.path_l[:-1])

        @property
        def color_id(self):
            if len(self.path_l) <= 2:
                return self.name
            else:
                return self.path_l[2]
        
        '''
        @property
        def rootless_parent(self):
            assert not self.ends_at_root()

            if len(self.path_l) == 2:
                return ''
            else:
                return ';'.join(self.path_l[1:-1])

        @property
        def rootless_path_s(self):
            assert not self.ends_at_root()

            return ';'.join(self.path_l[1:])



        def ends_at_root(self):
            return self.rank == ROOT_RANK

        '''


    @classmethod
    def build(cls) -> None:
        df = app_file.parse_truncated_fixRank()

        cls.nodes.clear()
        cls.num_records = df.shape[0]

        for row in df.iterrows():
            a = row[1].values # to np
            taxname_l = [ROOT_NAME] + list(a[a != None]) # to list with None vals truncated

            for i in range(len(taxname_l)):
                path_l = taxname_l[:i + 1]
                path_s = ';'.join(path_l)

                if path_s in cls.nodes:
                    node = cls.nodes[path_s]
                    node.count = node.count + 1
                else:
                    node = cls.Node(path_l)
                    cls.nodes[path_s] = node
                    node.count = node.count + 1

            node.num_leaf = node.num_leaf + 1

        cls.sanity_check()


    @classmethod
    def sanity_check(cls) -> None:

        ## Sanity checks
        num_leaves = 0
        for path_s, node in cls.nodes.items():
            num_leaves = num_leaves + node.num_leaf

        root = cls.nodes[ROOT_NAME]

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






