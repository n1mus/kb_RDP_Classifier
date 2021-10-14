import json

from pytest import raises

from kb_RDP_Classifier.util.debug import dprint
from kb_RDP_Classifier.impl.params import Params
from kb_RDP_Classifier.impl.globals import Var


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
        },
    })

    assert params['amp_mat_upa'] == '1/2/3'
    assert params['output_name'] == 'out_name'
    assert params.getd('conf') == 0.8
    assert params.getd('gene') == 'silva_138_ssu'
    assert(
        params.get_prose_args() == {
            'conf': '0.8',
            'gene': 'silva_138_ssu',
        }
    ), json.dumps(params.get_prose_args(), indent=4)
    assert(
        params.cli_args == [
            '--train_propfile',
            Var.propfile['silva_138_ssu'],
        ]
    ), params.cli_args

    str(params)  # should not throw


def test_non_default():
    params = Params({
        'workspace_id': 'ws_id',
        'amp_mat_upa': '5/5/5',
        'output_name': 'out_name',
        'rdp_clsf': {
            'conf': 0.99999,
            'gene': 'fungallsu',
        },
    })

    assert params['amp_mat_upa'] == '5/5/5'
    assert params['output_name'] == 'out_name'
    assert params.getd('conf') == 0.99999
    assert params.getd('gene') == 'fungallsu'
    assert(
        params.get_prose_args() == {
            'conf': '0.99999',
            'gene': 'fungallsu',
        }
    ), json.dumps(params.get_prose_args(), indent=4)
    assert(
        params.cli_args == [
            '--conf', '0.99999', '--gene', 'fungallsu',
        ]
    ), params.cli_args
    str(params)  # should not throw


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
    assert(
        params.get_prose_args() == {
            'conf': '0.8',
            'gene': 'silva_138_ssu',
        }
    ), json.dumps(params.get_prose_args(), indent=4)
    assert(
        params.cli_args == [
            '--train_propfile',
            Var.propfile['silva_138_ssu'],
        ]
    ), params.cli_args

    str(params)  # should not throw
