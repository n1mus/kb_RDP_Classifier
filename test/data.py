from unittest.mock import create_autospec
import os
import sys
import shutil
import logging
import json
from pathlib import Path
from functools import lru_cache

from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.KBaseReportClient import KBaseReport
from installed_clients.GenericsAPIClient import GenericsAPI

from kb_RDP_Classifier.util.cli import run_check
from kb_RDP_Classifier.util.debug import dprint
from kb_RDP_Classifier.impl.globals import Var

####################################################################################################
################################ CI ################################################################
####################################################################################################
enigma50by30 = '61042/5/1'
enigma50by30_noAttrMaps = '61042/6/1'
enigma50by30_noAttrMaps_tooShortSeqs = '61042/7/1'

ANL_amp = '61042/3/1'
ANL_amp_row_attributes = '61042/2/1'

userTest = '58225/2/1'

'''
enigma50by30_noAttrMaps = '55136/4/1'
enigma50by30_noAttrMaps_tooShortSeqs = '55136/6/1'

enigma50by30 = '55136/15/1'
enigma50by30_rowAttrMap = '55136/11/1'

enigma17770by511 = '55136/26/1'  # AmpliconMatrix
enigma17770by511_rowAttrMap = '55136/19/1'
'''
####################################################################################################
############################### appdev #############################################################
####################################################################################################



####################################################################################################
########################## dummy ###################################################################
####################################################################################################
dummy10by8_AmpMat_noRowAttrMap = 'dummy/10by8/AmpMat_noRowAttrMap'
dummy10by8_AmpMat_wRowAttrMap = 'dummy/10by8/AmpMat_wRowAttrMap'
dummy10by8_AttrMap = 'dummy/10by8/AttrMap'



TEST_DATA_DIR = '/kb/module/test/data'
GET_OBJECTS_DIR = TEST_DATA_DIR + '/get_objects'
FETCH_SEQUENCE_DIR = TEST_DATA_DIR + '/fetch_sequence'
WORK_DIR = '/kb/module/work/tmp'
CACHE_DIR = WORK_DIR + '/cache_test_data'

## MOCK GAPI ##

def mock_gapi_fetch_sequence(params):
    logging.info('Mocking `gapi.fetch_sequence(%s)`' % str(params))

    upa = ref_leaf(params)
    fp = _glob_upa(FETCH_SEQUENCE_DIR, upa)

    # Download and cache
    if fp is None:
        logging.info('Calling in cache mode `gapi.fetch_sequence(%s)`' % str(params))

        gapi = GenericsAPI(os.environ['SDK_CALLBACK_URL'], service_ver='dev')
        fp_work = gapi.fetch_sequence(params)
        fp_cache = os.path.join(
            mkcache(FETCH_SEQUENCE_DIR),
            file_safe_ref(upa) + '.fa'
        )
        shutil.copyfile(
            fp_work,
            fp_cache
        )
        return fp_work

    # Pull from cache
    else:
        return fp


def get_mock_gapi():
    mock_gapi = create_autospec(GenericsAPI, instance=True)
    mock_gapi.fetch_sequence.side_effect = mock_gapi_fetch_sequence
    return mock_gapi

mock_gapi = get_mock_gapi()


## MOCK DFU ##

def mock_dfu_save_objects(params):
    logging.info('Mocking dfu.save_objects(%s)' % str(params)[:200] + '...' if len(str(params)) > 200 else params)

    return [['mock', 1, 2, 3, 'dfu', 5, 'save_objects']]  # UPA made from pos 6/0/4

def mock_dfu_get_objects(params):
    logging.info('Mocking `dfu.get_objects(%s)`' % params)

    upa = ref_leaf(params['object_refs'][0])
    fp = _glob_upa(GET_OBJECTS_DIR, upa)

    # Download and cache
    if fp is None:
        logging.info('Calling in cache mode `dfu.get_objects`')

        dfu = DataFileUtil(os.environ['SDK_CALLBACK_URL'])
        obj = dfu.get_objects(params)
        fp = os.path.join(
            mkcache(GET_OBJECTS_DIR),
            file_safe_ref(upa) + TRANSFORM_NAME_SEP + obj['data'][0]['info'][1] + '.json'
        )
        with open(fp, 'w') as fh: json.dump(obj, fh)
        return obj

    # Pull from cache
    else:
        with open(fp) as fh:
            obj = json.load(fh)
        return obj


def get_mock_dfu():
    mock_dfu = create_autospec(DataFileUtil, instance=True, spec_set=True)
    mock_dfu.save_objects.side_effect = mock_dfu_save_objects
    mock_dfu.get_objects.side_effect = mock_dfu_get_objects
    return mock_dfu

mock_dfu = get_mock_dfu()



## MOCK RUN_CHECK

def get_mock_run_check(dataset, non_default_gene=False):
    '''
    Avoid expensive runs of tool
    Copy over `Var.out_dir`
    '''
    mock_run_check = create_autospec(run_check)

    # side effect
    def mock_run_check_(cmd):
        logging.info('Mocking running cmd `%s`' % cmd)

        ret_dir = 'return'
        if non_default_gene is not False:
             ret_dir += '_' + non_default_gene

        # test data
        src_drpth = os.path.join(TEST_DATA_DIR, 'return', dataset, ret_dir, 'RDP_Classifier_output')

        # check if it already exists
        # since app may create it before run, and
        # since `check_run` is called twice in this app
        if os.path.exists(Var.out_dir):
            shutil.rmtree(Var.out_dir)
        shutil.copytree(src_drpth, Var.out_dir)


    mock_run_check.side_effect = mock_run_check_

    return mock_run_check


## MOCK KBR ##

def mock_create_extended_report(params):
    logging.info('Mocking `kbr.create_extended_report`')

    return {
        'name': 'kbr_mock_name',
        'ref': 'kbr/mock/ref',
    }

mock_kbr = create_autospec(KBaseReport, instance=True, spec_set=True)
mock_kbr.create_extended_report.side_effect = mock_create_extended_report

## UTIL ##

def mkcache(dir):
    dir = dir.replace(TEST_DATA_DIR, CACHE_DIR)
    os.makedirs(dir, exist_ok=True)
    return dir

def _glob_upa(data_dir, upa):
    p_l = list(Path(data_dir).glob(file_safe_ref(upa) + '*'))
    if len(p_l) == 0:
        return None
    elif len(p_l) > 1:
        raise Exception(upa)

    src_p = str(p_l[0])

    return src_p

def ref_leaf(ref):
    return ref.split(';')[-1]

def file_safe_ref(ref):
    return ref.replace('/', '.').replace(';', '_')

TRANSFORM_NAME_SEP = '_'
