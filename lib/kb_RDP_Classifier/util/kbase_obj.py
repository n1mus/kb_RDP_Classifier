import logging
import pandas as pd
import numpy as np
import os
import sys
import gzip
import re

from .dprint import dprint
from .config import Var
from .error import * # exceptions and msgs


pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 20)



# TODO inheritance



####################################################################################################
####################################################################################################
####################################################################################################

class AmpliconSet:

    OBJ_TYPE = "KBaseExperiments.AmpliconSet"

    def __init__(self, upa):
        self.upa = upa

        self._get_obj()


    def _get_obj(self):
        logging.info('Loading object data for %s' % self.upa)

        obj = Var.dfu.get_objects({
            'object_refs': [self.upa]
            })
        
        self.name = obj['data'][0]['info'][1]
        self.obj = obj['data'][0]['data']
        self.amp_mat_upa = self.obj['amplicon_matrix_ref']


    def to_fasta(self, fasta_flpth):
        
        logging.info(f'Writing fasta to {fasta_flpth}')

        amplicon_d = self.obj['amplicons']
        
        with open(fasta_flpth, 'w') as fh:
            for i, (id, d) in enumerate(amplicon_d.items()):
                fh.write('>' + id + '\n')
                fh.write(d['consensus_sequence'] + '\n')


    def write_taxonomy(self, id2taxStr_d, overwrite):
        '''
        If `overwrite`: overwrite
        If not `overwrite`: only write if all empty 
        '''
        empty_tax = True
        for amplicon_d in self.obj['amplicons'].values():
            if len(amplicon_d['taxonomy']) > 0:
                empty_tax = False
                break

        if not empty_tax:
            if overwrite:
                msg = (
                    'Input AmpliconSet with name %s has non-empty taxonomy fields. '
                    'Overwriting since `overwrite` was selected'
                    % self.name
                )
                logging.warning(msg)
                Var.warnings.append(msg)
            else:
                msg = (
                    'Input AmpliconSet with name %s has non-empty taxonomy fields. '
                    'Not overwriting since `do_not_overwrite` was selected'
                    % self.name
                )
                logging.warning(msg)
                Var.warnings.append(msg)
                return

 
        for id, amplicon_d in self.obj['amplicons'].items():
            amplicon_d['taxonomy'] = {
                'lineage': [taxname for taxname in id2taxStr_d[id].split(';') if len(taxname) > 0],
                'taxonomy_source': 'rdp',
            }

        if Var.debug:        
            assert self._is_all_assigned_taxonomy()


        
    def update_amplicon_matrix_ref(self, amp_mat_upa_new):
        self.obj['amplicon_matrix_ref'] = amp_mat_upa_new


    def save(self, name=None):

        logging.info('Saving %s' % self.OBJ_TYPE)

        info = Var.dfu.save_objects({
            "id": Var.params['workspace_id'],
            "objects": [{
                "type": self.OBJ_TYPE,
                "data": self.obj,
                "name": name if name is not None else self.name,
                #"extra_provenance_input_refs": [self.upa], # don't need if original version is input
             }]
        })[0]

        upa_new = "%s/%s/%s" % (info[6], info[0], info[4])

        return upa_new


    def _is_all_assigned_taxonomy(self):
        for amplicon_d in self.obj['amplicons'].values():
            if len(amplicon_d) == 0:
                return False
        return True



####################################################################################################
####################################################################################################
####################################################################################################

class AmpliconMatrix:

    OBJ_TYPE = "KBaseMatrices.AmpliconMatrix"

    def __init__(self, upa):
        self.upa = upa

        self._get_obj()
        self._get_row_attributemapping_ref()


    def _get_obj(self):
        obj = Var.dfu.get_objects({
            'object_refs': [self.upa]
            })

        self.name = obj['data'][0]['info'][1]
        self.obj = obj['data'][0]['data']

    def _get_row_attributemapping_ref(self):
        self.row_attrmap_upa = self.obj.get('row_attributemapping_ref')
        if self.row_attrmap_upa == None:
            msg = (
                "Input AmpliconSet's AmpliconMatrix does not have a row AttributeMapping to assign traits to. "
                "A new row AttributeMapping will be created"
            )
            logging.warning(msg)
            Var.warnings.append(msg)


    def update_row_attributemapping_ref(self, row_attrmap_upa_new):
        self.obj['row_attributemapping_ref'] = row_attrmap_upa_new


    def save(self, name=None):

        info = Var.dfu.save_objects({
            "id": Var.params['workspace_id'],
            "objects": [{
                "type": self.OBJ_TYPE,
                "data": self.obj,
                "name": name if name else self.name,
                "extra_provenance_input_refs": [self.upa],
             }]})[0]

        upa_new = "%s/%s/%s" % (info[6], info[0], info[4])

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
            (A) If creating self from scratch, need to know `row_ids`
            (B) AttributeMapping ids >= AmpliconMatrix ids (for row or col)
                and only a subset of AttributeMapping may be assigned
        """
        self.upa = upa
        self.amp_mat = amp_mat

        if upa is not None:
            self._get_obj()
        else:
            self._get_obj_new()



    def _get_obj(self):
        obj = Var.dfu.get_objects({
            'object_refs': [self.upa]
            })

        self.name = obj['data'][0]['info'][1]
        self.obj = obj['data'][0]['data']


    def _get_obj_new(self):
        
        id_l = self.amp_mat.obj['data']['row_ids']

        instances = {id: [] for id in id_l}

        self.obj = {
            'attributes': [],
            'instances': instances,
            'ontology_mapping_method': 'User curated',
        }

        self.name = self.amp_mat.name + '.row_AttributeMapping' # TODO length checks



    def get_attribute_slot(self, attribute: str, source: str) -> int:

        d = {'attribute': attribute, 'source': source}

        ind = -1 # if `attributes` list is empty

        # check if already exists
        for ind, attr_d in enumerate(self.obj['attributes']):
            if attr_d == d:
                msg = (
                    'Row AttributeMapping with name `%s` '
                    'already has field with attribute `%s` and source `%s`. '
                    'This field will be overwritten'
                    % (self.name, attribute, source)
                )
                logging.warning(msg)
                Var.warnings.append(msg)
                return ind

        # append slot to `attributes`
        self.obj['attributes'].append(d)

        # append slots to `instances` 
        for attr_l in self.obj['instances'].values():
            attr_l.append('')

        return ind + 1



    def update_attribute(self, ind, id2attr_d):

        # fill slots in `instances`
        for id, attr_l in self.obj['instances'].items():
            attr_l[ind] = id2attr_d.get(id, '')




    def save(self, name=None):
        logging.info('Saving %s' % self.OBJ_TYPE)

        obj = {
            "type": self.OBJ_TYPE,
            "data": self.obj,
            "name": name if name else self.name,
         }

        if self.upa:
            obj["extra_provenance_input_refs"] = [self.upa]

        info = Var.dfu.save_objects({ 
            "id": Var.params['workspace_id'],
            "objects": [obj]
            })[0]

        upa_new = "%s/%s/%s" % (info[6], info[0], info[4])

        return upa_new


    def is_tax_populated_looks_normal(self, ind):
        """
        For testing
        Make sure that attribute is present, and all AmpliconSet id's are assigned for
        Doesn't work for every case since RDP skips assigning for too short sequences
        """
        
        num_attr = len(self.obj['attributes'])

        for id, instance in self.obj['instances'].items():
            assert len(instance) == num_attr
            if id in self.amp_mat.obj['data']['row_ids']:
                assert re.match('(.+;){6}$', instance[ind]), 'attribute is `%s`' % instance[ind]

        return True

