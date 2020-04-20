import logging
import pandas as pd
import numpy as np
import os
import sys
import gzip

from .dprint import dprint
from .config import _globals
from .error import *



pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 20)



# TODO DRY <-- inheritance



####################################################################################################
####################################################################################################
####################################################################################################

class AmpliconSet:

    OBJ_TYPE = "KBaseExperiments.AmpliconSet"

    def __init__(self, upa, mini_data=False):
        self.upa = upa
        self.mini_data = mini_data

        self._get_obj()


    def _get_obj(self):
        logging.info('Loading object data for %s' % self.upa)

        obj = _globals.dfu.get_objects({
            'object_refs': [self.upa]
            })
        
        self.name = obj['data'][0]['info'][1]
        self.obj = obj['data'][0]['data']
        self.amp_mat_upa = self.obj['amplicon_matrix_ref']


    def to_fasta(self, fasta_flnm='study_seqs.fna'):
        fasta_flpth = os.path.join(_globals.run_dir, fasta_flnm)
        
        logging.info(f'Writing fasta to {fasta_flpth}')

        amplicon_d = self.obj['amplicons']
        
        with open(fasta_flpth, 'w') as fp:
            for i, (id, d) in enumerate(amplicon_d.items()):
                fp.write('>' + id + '\n')
                fp.write(d['consensus_sequence'] + '\n')

                if _globals.debug and self.mini_data and i > 20:
                    break
              
        self.fasta_flpth = fasta_flpth


    def update_amplicon_matrix_ref(self, amp_mat_upa_new):
        self.obj['amplicon_matrix_ref'] = amp_mat_upa_new


    def save(self, name=None):

        logging.info('Saving %s' % self.OBJ_TYPE)

        info = _globals.dfu.save_objects({
            "id": _globals.params['workspace_id'],
            "objects": [{
                "type": self.OBJ_TYPE,
                "data": self.obj,
                "name": name if name else self.name,
                "extra_provenance_input_refs": [self.upa], # TODO remove if AmpliconSet is input?
             }]})[0]

        upa_new = "%s/%s/%s" % (info[6], info[0], info[4])

        return upa_new




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
        obj = _globals.dfu.get_objects({
            'object_refs': [self.upa]
            })

        self.name = obj['data'][0]['info'][1]
        self.obj = obj['data'][0]['data']

    def _get_row_attributemapping_ref(self):
        self.row_attr_map_upa = self.obj.get('row_attributemapping_ref')
        if self.row_attr_map_upa == None:
            raise NoWorkspaceReferenceException(
                'AmpliconSet\'s associated AmpliconMatrix does not have associated row AttributeMapping to assign traits to.')


    def update_row_attributemapping_ref(self, row_attr_map_upa_new):
        self.obj['row_attributemapping_ref'] = row_attr_map_upa_new


    def save(self, name=None):

        info = _globals.dfu.save_objects({
            "id": _globals.params['workspace_id'],
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

    OBJ_TYPE = "KBaseExperiments.AttributeMapping"

    def __init__(self, upa, mini_data=False):
        self.upa = upa
        self.mini_data = mini_data

        self._get_obj()

    def _get_obj(self):
        obj = _globals.dfu.get_objects({
            'object_refs': [self.upa]
            })

        self.name = obj['data'][0]['info'][1]
        self.obj = obj['data'][0]['data']


    @staticmethod
    def parse_filterByConf(filterByConf_flpth) -> dict:
        
        df = pd.read_csv(filterByConf_flpth, sep='\t', index_col=0)
        id2taxStr_d = df.apply(lambda row: ';'.join(row.array), axis=1).to_dict()

        return id2taxStr_d


        
    def update_attribute(self, id2attr_d, attribute, source):

        # find index of attribute
        for ind, attr_d in enumerate(self.obj['attributes']):
            if attr_d['attribute'] == attribute:
                attr_ind = ind
                break

        # fill slots in `instances`
        for id, attr_l in self.obj['instances'].items():
            attr_l[attr_ind] = id2attr_d.get(id, '')

        self.obj['attributes'][attr_ind]['source'] = source



    def add_attribute_slot(self, attribute):
        
        # check if already exists
        for attr_d in self.obj['attributes']:
            if attr_d['attribute'] == attribute:
                msg = 'Adding attribute slot %s to AttributeMapping with name %s, ' + \
                      'but that attribute already exists in object' % (attribute, self.name)
                logging.warnings(msg)
                _globals.warnings.append(msg)
                return

        # append slot to `attributes`
        self.obj['attributes'].append({
            'attribute': attribute,
            })

        # append slots to `instances` 
        for _, attr_l in self.obj['instances'].items():
            attr_l.append('')



    def save(self, name=None):
        logging.info('Saving %s' % self.OBJ_TYPE)

        info = _globals.dfu.save_objects({
            "id": _globals.params['workspace_id'],
            "objects": [{
                "type": self.OBJ_TYPE,
                "data": self.obj,
                "name": name if name else self.name,
                "extra_provenance_input_refs": [self.upa],
             }]})[0]

        upa_new = "%s/%s/%s" % (info[6], info[0], info[4])

        return upa_new


       



