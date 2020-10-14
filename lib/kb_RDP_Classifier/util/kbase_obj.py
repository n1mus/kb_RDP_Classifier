import logging
import pandas as pd
import numpy as np
import os
import sys
import gzip
import re
import json

from .dprint import dprint
from .config import Var
from .error import * # exceptions and msgs


pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 20)


def write_json(obj, flnm, AmpliconSet=False):  # TODO nix this but keep the annotate with AmpMat name                                                 
    '''                                                                                             
    For debugging/testing                                                                           
    '''                                                                                             
    if 'run_dir' not in Var:                                                                        
        import uuid                                                                                 
        Var.run_dir = os.path.join('/kb/module/work/tmp', str(uuid.uuid4()))                        
        os.mkdir(Var.run_dir)                                                                       
                                                                                                    
    flpth = os.path.join(Var.run_dir, flnm)                                                         
    with open(flpth, 'w') as f:                                                                     
        json.dump(obj, f, indent=3)                                                                 
                                                                                                    
    if AmpliconSet == True:                                                                         
        dprint('touch %s' % os.path.join(Var.run_dir, '#' + obj['data'][0]['info'][1]), run='cli') # annotate run_dir with name
                                                                                                    
  


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

        if Var.debug: write_json(obj, 'get_objects_AmpliconMatrix.json')

        self.name = obj['data'][0]['info'][1]
        self.obj = obj['data'][0]['data']

    @property 
    def row_attrmap_upa(self):
        row_attrmap_upa = self.obj.get('row_attributemapping_ref')
        if row_attrmap_upa is None: # TODO move this logic to impl
            msg = (
                "Input AmpliconMatrix does not have a row AttributeMapping to assign traits to. "
                "A new row AttributeMapping will be created"
            )
            if msg not in Var.warnings:
                logging.warning(msg)
                Var.warnings.append(msg)

        return row_attrmap_upa

    def get_fasta(self):
        dprint('self.upa', run=locals())
        fasta_flpth = Var.gapi.fetch_sequence(self.upa)
        return fasta_flpth


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
            'object_refs': [self.upa]
            })

        if Var.debug: write_json(obj, 'get_objects_AttributeMapping.json')

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

        self.name = self.amp_mat.name + '.row_AttrMap' # TODO length checks



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
        '''
        For updating the taxonomy attribute
        '''

        # fill slots in `instances`
        for id, attr_l in self.obj['instances'].items():
            attr_l[ind] = id2attr_d[id]


    def save(self, name=None):
        logging.info('Saving %s' % self.OBJ_TYPE)

        obj = {
            "type": self.OBJ_TYPE,
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




    # TODO move to testing
    '''
    def _is_tax_populated_looks_normal(self, ind): 
        """
        For testing
        Make sure that attribute is present, and all AmpliconSet id's are assigned for
        Doesn't work for every case since RDP skips assigning for too short sequences
        """
        
        num_attr = len(self.obj['attributes'])

        for id, instance in self.obj['instances'].items():
            assert len(instance) == num_attr
            if id in self.amp_mat.obj['data']['row_ids']:
                if id in Var.shortSeq_id_l:
                    assert instance[ind] == ''
                else:
                    assert re.match('(.+;){6}$', instance[ind]), 'attribute is `%s`' % instance[ind]

        return True
    '''

