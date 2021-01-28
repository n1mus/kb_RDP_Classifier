import os
import unittest
from unittest.mock import patch
import json
import uuid
import numpy as np
from pytest import raises

from kb_RDP_Classifier.util.debug import dprint, where_am_i
from kb_RDP_Classifier.impl.globals import Var
from kb_RDP_Classifier.impl.params import Params
from kb_RDP_Classifier.impl.kbase_obj import AmpliconMatrix, AttributeMapping
from kb_RDP_Classifier.impl import report
from data import *
from config import *


####################
####################
@patch.dict('kb_RDP_Classifier.impl.kbase_obj.Var', values={'dfu': get_mock_dfu('dummy10by8'), 'warnings': []})
def test_wRowAttrMap():
    '''
    Test row AttributeMapping behavior when AmpliconMatrix has row AttributeMapping
    Row AttributeMapping indices should be in sync with AmpliconMatrix indices (1 to 1)
    '''
    Var.run_dir = os.path.join(
        scratch, 
        'test_AmpliconMatix_wRowAttributeMapping_AttributeMapping_' + str(uuid.uuid4())
    )

    amp_mat = AmpliconMatrix(dummy10by8_AmpMat_wRowAttrMap)
    assert len(Var.warnings) == 0

    attr_map = AttributeMapping(amp_mat.obj.get('row_attributemapping_ref'), amp_mat) # has attributes `biome` and `celestial body`

    ##
    ## write new attribute
    ind_0, attr_name_0 = attr_map.add_attribute_slot('color', 'testing')
    assert ind_0 == 2
    assert attr_name_0 == 'color', json.dumps(attr_map.obj, indent=3)

    attr_map.update_attribute(ind_0, {
        "amplicon_id_0": "dummy0",
        "amplicon_id_1": "dummy0",
        "amplicon_id_2": "dummy0",
        "amplicon_id_3": "dummy0",
        "amplicon_id_4": "dummy0",
        "amplicon_id_5": "dummy0",
        "amplicon_id_6": "dummy0",
        "amplicon_id_7": "dummy0",
        "amplicon_id_8": "dummy0",
        "amplicon_id_9": "dummy0"
    })

    assert attr_map.obj['instances']['amplicon_id_4'][ind_0] == 'dummy0'

    ##
    ## write duplicate attribute
    ind_1, attr_name_1 = attr_map.add_attribute_slot('celestial body', 'upload')
    assert ind_1 == 3, json.dumps(attr_map.obj, indent=3)
    assert attr_name_1 == 'celestial body (1)', json.dumps(attr_map.obj, indent=3)

    attr_map.update_attribute(ind_1, {
        "amplicon_id_0": "dummy1",
        "amplicon_id_1": "dummy1",
        "amplicon_id_2": "dummy1",
        "amplicon_id_3": "dummy1",
        "amplicon_id_4": "dummy1",
        "amplicon_id_5": "dummy1",
        "amplicon_id_6": "dummy1",
        "amplicon_id_7": "dummy1",
        "amplicon_id_8": "dummy1",
        "amplicon_id_9": "dummy1"
    })

    ##
    ## all same length
    num_attr = len(attr_map.obj['attributes'])
    for attr_l in attr_map.obj['instances'].values():
        assert len(attr_l) == num_attr

    ## 
    ## check did not add dummy attribute to wrong slot
    ind_lftvr = list(set(range(num_attr)) - {ind_0, ind_1})

    for attr_l in attr_map.obj['instances']:
        for ind in ind_lftvr:
            assert 'dummy' not in attr_l[ind]


####################
####################
@patch.dict('kb_RDP_Classifier.impl.kbase_obj.Var', values={'dfu': get_mock_dfu('dummy10by8')})
def test_noRowAttrMap():
    '''
    Test row AttributeMapping behavior when AmpliconMatrix has no row AttributeMapping
    '''
    Var.run_dir = os.path.join(
        scratch, 
        'test_AmpliconMatix_noRowAttributeMapping_AttributeMapping_' + str(uuid.uuid4())
    )
    Var.params = Params(dict(
        workspace_id='ws_id',
        workspace_name='ws_name',
        amp_mat_upa='amp/mat/upa',
        output_name='out_name',
    ))

    amp_mat = AmpliconMatrix(dummy10by8_AmpMat_noRowAttrMap)
    attr_map = AttributeMapping(amp_mat.obj.get('row_attributemapping_ref'), amp_mat)

    ##
    ## write new attribute/source
    ind_0, attr_name_0 = attr_map.add_attribute_slot('biome', 'testing')
    assert ind_0 == 0
    assert attr_name_0 == 'biome', json.dumps(attr_map.obj, indent=3)

    attr_map.update_attribute(ind_0, {
        "amplicon_id_0": "dummy0",
        "amplicon_id_1": "dummy0",
        "amplicon_id_2": "dummy0",
        "amplicon_id_3": "dummy0",
        "amplicon_id_4": "dummy0",
        "amplicon_id_5": "dummy0",
        "amplicon_id_6": "dummy0",
        "amplicon_id_7": "dummy0",
        "amplicon_id_8": "dummy0",
        "amplicon_id_9": "dummy0"
    })

    assert attr_map.obj['instances']['amplicon_id_4'][ind_0] == 'dummy0'

    ##
    ## all same length
    num_attr = len(attr_map.obj['attributes'])
    for attr_l in attr_map.obj['instances'].values():
        assert len(attr_l) == num_attr



