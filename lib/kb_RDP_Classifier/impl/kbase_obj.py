import logging
import pandas as pd
import numpy as np
import os
import sys
import gzip
import re
import json

from ..util.debug import dprint
from ..util.misc import get_numbered_duplicate
from .globals import Var


pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 20)




####################################################################################################
####################################################################################################
####################################################################################################

class AmpliconMatrix:


    OBJ_TYPE = "KBaseMatrices.AmpliconMatrix"


    def __init__(self, upa):
        self.upa = upa
        self._get_obj()


    def _get_obj(self):
        obj = Var.dfu.get_objects({
            'object_refs': [self.upa]
            })

        self.name = obj['data'][0]['info'][1]
        self.obj = obj['data'][0]['data']

        # debug annotate run_dir with name
        if 'run_dir' in Var:
            dprint('touch %s' % os.path.join(Var.run_dir, '_' + self.name), run='cli')

    def get_fasta(self):
        fasta_flpth = Var.gapi.fetch_sequence(self.upa)
        return fasta_flpth


    def add_row_mapping(self):
        self.obj['row_mapping'] = {
            id: id for id in self.obj['data']['row_ids']
        }


    def _swap_ids(self, id2attr: dict, axis='row') -> dict:
        '''
        `id2attr` will be AmpliconMatrix ids to attribute
        Swap those ids out for the AttributeMapping ids
        '''
        if f'{axis}_mapping' not in self.obj:  # row_mapping conditionally required with row_attributemapping_ref
            return id2attr                    # but if not present, then probably not needed anyway

        id2attr = {
            self.obj[f'{axis}_mapping'][id]: attr
            for id, attr in id2attr.items()
        }

        return id2attr


    def save(self, name=None):

        logging.info('Saving AmpliconMatrix using Generics API')

        upa_new = Var.gapi.save_object({
            'obj_type': self.OBJ_TYPE,  # TODO version
            'obj_name': name if name else self.name,
            'data': self.obj,
            'workspace_id': Var.params['workspace_id'],
        })['obj_ref']

        return upa_new



####################################################################################################
####################################################################################################
####################################################################################################

class AttributeMapping:
    '''
    For AmpliconMatrix's row AttributeMapping
    '''


    OBJ_TYPE = "KBaseExperiments.AttributeMapping"


    def __init__(self, upa, amp_mat: AmpliconMatrix):
        """
        Input
        -----
        amp_mat
            required because
            (A) If creating self from scratch, need to know `row_ids` and `name`
            (B) AttributeMapping ids >= AmpliconMatrix ids (for row or col)
                and only a subset of AttributeMapping may be assigned.
                So you want to know that for testing
        """
        self.upa = upa
        self.amp_mat = amp_mat

        if upa is not None:
            self._get_obj()
        else:
            self._get_obj_new()


    def _get_obj(self):
        obj = Var.dfu.get_objects({
            'object_refs': ['%s;%s' % (self.amp_mat.upa, self.upa)]
            })

        self.name = obj['data'][0]['info'][1]
        self.obj = obj['data'][0]['data']


    def _get_obj_new(self):
        self.amp_mat.add_row_mapping()  # row_mapping is conditionally required with row_attributemapping_ref

        id_l = self.amp_mat.obj['data']['row_ids']

        instances = {id: [] for id in id_l}

        self.obj = {
            'attributes': [],
            'instances': instances,
            'ontology_mapping_method': 'User curated',
        }


    def get_attribute_names(self):
        return [d['attribute'] for d in self.obj['attributes']]


    def add_attribute_slot(self, attribute, source) -> tuple:
        '''
        Return index and name
        '''

        # get new name if it's a duplicate
        attributes = [d['attribute'] for d in self.obj['attributes']]
        if attribute in attributes:
            attribute = get_numbered_duplicate(attributes, attribute)

        # append slots
        self.obj['attributes'].append({
            'attribute': attribute,
            'source': source,
        })
        for instance in self.obj['instances'].values():
            instance.append(None)
        #
        return len(self.obj['attributes']) - 1, attribute


    def update_attribute(self, ind, id2attr):
        '''
        For updating the taxonomy attribute
        '''
        # swap AmpMat ids for rowAttrMap ones
        id2attr = self.amp_mat._swap_ids(id2attr, axis='row')

        # fill slots in `instances`
        for id, attr_l in self.obj['instances'].items():
            attr_l[ind] = id2attr[id]


    def save(self, name=None):
        logging.info('Saving %s' % self.OBJ_TYPE)

        obj = {
            "type": self.OBJ_TYPE,  # TODO version
            "data": self.obj,
            "name": name if name is not None else self.name,
        }

        # if there is an input row AttributeMapping
        if self.upa is not None:
            obj["extra_provenance_input_refs"] = [self.upa]

        info = Var.dfu.save_objects({
            "id": Var.params['workspace_id'],
            "objects": [obj]
            })[0]

        upa_new = "%s/%s/%s" % (info[6], info[0], info[4])

        return upa_new




