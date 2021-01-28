import os
import unittest
from unittest.mock import patch
import json
import uuid
import numpy as np
from pytest import raises

from kb_RDP_Classifier.util.debug import dprint, where_am_i
from kb_RDP_Classifier.impl.params import Params
from kb_RDP_Classifier.impl.globals import Var
from kb_RDP_Classifier.impl.kbase_obj import AmpliconMatrix, AttributeMapping
from data import *






def test_validation():

    p = dict(
        workspace_id=None,
        amp_mat_upa=None,
        rdp_clsf=dict(
            gene=None,
            conf=None,
        ),
        output_name=None,
    )
    Params(p)

    p = dict(
        workspace_id=None,
        amp_mat_upa=None,
        rdp_clsf=dict(
            gene=None,
            conf=None,
        ),
        outptu_name=None,
    )
    with raises(Exception): Params(p)


def test_flatten():

    d = {
        'key0': 'hat',
        'key1': 'bat',
        'nest0': {
            'key2': 'cat',
            'key3': 'sat',
        },
        'key4': 'chat',
        'nest1': {
            'key5': 'gnat',
        },
        'key6': 'mat',
    }

    flatd = Params.flatten(d)

    assert len(flatd) == 7
    assert all(['key%d' % i in flatd for i in range(7)])
    assert all(['nest%d' % i not in flatd for i in range(2)])
    assert flatd['key5'] == 'gnat'



def test_default():
    params = Params({
        'workspace_id': 'ws_id',
        'amp_mat_upa': '1/2/3',
        'output_name': 'out_name',
        'rdp_clsf': {
            'conf': 0.8,
            'gene': 'silva_138_ssu',
            'minWords': None,
        },
    })

    assert params['amp_mat_upa'] == '1/2/3'
    assert params['output_name'] is 'out_name'
    assert params.getd('conf') == 0.8
    assert params.getd('gene') == 'silva_138_ssu'
    assert params.getd('minWords') is None
    assert(
        params.get_prose_args() == {
            'conf': '0.8',
            'gene': 'silva_138_ssu',
            'minWords': 'default'
        }
    ), json.dumps(params.get_prose_args(), indent=4)
    assert(
        params.cli_args == [
            '--train_propfile', 
            '/kb/module/data/SILVA_138_SSU_NR_99/rRNAClassifier.properties'
        ]
    ), params.cli_args
    
    str(params) # should not throw

def test_non_default():
    params = Params({
        'workspace_id': 'ws_id',
        'amp_mat_upa': '5/5/5',
        'output_name': 'out_name',
        'rdp_clsf': {
            'conf': 0.99999,
            'gene': 'fungallsu',
            'minWords': 100,
        },
    })

    assert params['amp_mat_upa'] == '5/5/5'
    assert params['output_name'] == 'out_name'
    assert params.getd('conf') == 0.99999
    assert params.getd('gene') == 'fungallsu'
    assert params.getd('minWords') == 100
    assert(
        params.get_prose_args() == {
            'conf': '0.99999',
            'gene': 'fungallsu',
            'minWords': '100'
        }
    ), json.dumps(params.get_prose_args(), indent=4)
    assert(
        params.cli_args == [
            '--conf', '0.99999', '--gene', 'fungallsu', '--minWords', '100'
        ] 
    ), params.cli_args
    str(params) # should not throw


def test_no_user_supplied_values():
    params = Params({
        'workspace_id': 'ws_id',
        'amp_mat_upa': '6/6/6',
        'output_name': 'out_name',
    })

    assert params['amp_mat_upa'] == '6/6/6'
    assert params['output_name'] == 'out_name'
    assert params.getd('conf') == 0.8
    assert params.getd('gene') == 'silva_138_ssu'
    assert params.getd('minWords') is None
    assert(
        params.get_prose_args() == {
            'conf': '0.8',
            'gene': 'silva_138_ssu',
            'minWords': 'default'
        }
    ), json.dumps(params.get_prose_args(), indent=4)
    assert(
        params.cli_args == [
            '--train_propfile', 
            '/kb/module/data/SILVA_138_SSU_NR_99/rRNAClassifier.properties'
        ]
    ), params.cli_args
    
    str(params) # should not throw



