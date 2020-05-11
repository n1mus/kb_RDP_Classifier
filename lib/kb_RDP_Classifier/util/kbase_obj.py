import logging
import pandas as pd
import numpy as np
import os
import sys
import gzip
import re

from .dprint import dprint
from .config import _globals
from .error import * # *Exception
from .message import *



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

    """
    def write_taxonomy(self, id2taxStr_d, overwrite):
        '''
        If `overwrite`: overwrite
        If not `overwrite`: only write empty ones
        '''
        for id_, amplicon_d in self.obj['amplicons'].items():
            if len(amplicon_d['taxonomy']) == 0 or overwrite:
                amplicon_d['taxonomy'] = {
                    'lineage': [taxon.strip() for taxon in id2taxStr_d[id_].split(';')],
                    'taxonomy_source': 'rdp',
                }

        if _globals.debug:        
            assert self._is_all_assigned_taxonomy()
    """


    def write_taxonomy(self, id2taxStr_d, overwrite):
        '''
        If `overwrite`: overwrite
        If not `overwrite`: only write if all empty 
        '''
        if not overwrite:
            for amplicon_d in self.obj['amplicons'].values():
                if len(amplicon_d['taxonomy']) > 0:
                    logging.warning(msg_notOverwriting)
                    _globals.warnings.append(msg_notOverwriting)
                    return

        for id_, amplicon_d in self.obj['amplicons'].items():
            amplicon_d['taxonomy'] = {
                'lineage': [taxon.strip() for taxon in id2taxStr_d[id_].split(';')],
                'taxonomy_source': 'rdp',
            }

        if _globals.debug:        
            assert self._is_all_assigned_taxonomy()



        
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
        obj = _globals.dfu.get_objects({
            'object_refs': [self.upa]
            })

        self.name = obj['data'][0]['info'][1]
        self.obj = obj['data'][0]['data']

    def _get_row_attributemapping_ref(self):
        self.row_attrmap_upa = self.obj.get('row_attributemapping_ref')
        if self.row_attrmap_upa == None:
            logging.warning(msg_createNewRowAttributeMapping)
            _globals.warnings.append(msg_createNewRowAttributeMapping)


    def update_row_attributemapping_ref(self, row_attrmap_upa_new):
        self.obj['row_attributemapping_ref'] = row_attrmap_upa_new


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

    def __init__(self, upa, amp_mat: AmpliconMatrix, mini_data=False):
        """
        Input:
            amp_mat - required because AttributeMapping ids >= AmpliconMatrix ids (for row or col)
                      and only a subset of AttributeMapping may be assigned
        """
        self.upa = upa
        self.amp_mat = amp_mat
        self.mini_data = mini_data

        if upa:
            self._get_obj()
        elif upa == None:
            self._get_obj_new()
        else:
            raise Exception()



    def _get_obj(self):
        obj = _globals.dfu.get_objects({
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
        for id_, attr_l in self.obj['instances'].items():
            attr_l[attr_ind] = id2attr_d.get(id_, '')

        self.obj['attributes'][attr_ind]['source'] = source

        if _globals.debug:
            assert self._is_populated_looks_normal(attribute, source)



    def add_attribute_slot(self, attribute):
        
        # check if already exists
        for attr_d in self.obj['attributes']:
            if attr_d['attribute'] == attribute:
                msg = msg_attrAlreadyExists % (attribute, self.name) # TODO take out of error.py
                logging.warning(msg)
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

        object_ = {
            "type": self.OBJ_TYPE,
            "data": self.obj,
            "name": name if name else self.name,
             }

        if self.upa:
            object_["extra_provenance_input_refs"] = [self.upa]

        info = _globals.dfu.save_objects({ # TODO consolidate calls for performance?
            "id": _globals.params['workspace_id'],
            "objects": [object_]
            })[0]

        upa_new = "%s/%s/%s" % (info[6], info[0], info[4])

        return upa_new


    def _is_populated_looks_normal(self, attribute, source):
        """
        Make sure that attribute is present, and all AmpliconSet id's are assigned for
        """
        
        ind = -1
        for ind_, attr_d in enumerate(self.obj['attributes']):
            if attr_d['attribute'] == attribute:
                ind = ind_
                assert attr_d['source'] == source

        if ind == -1:
            return False

        num_attr = len(self.obj['attributes'])

        for id_, instance in self.obj['instances'].items():
            assert len(instance) == num_attr
            if id_ in self.amp_mat.obj['data']['row_ids']:
                assert re.match('(.+;){5}.+', instance[ind]), 'attribute is `' + instance[ind] + '`' # TODO more precise

        return True

