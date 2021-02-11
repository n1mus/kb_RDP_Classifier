from unittest.mock import create_autospec
import os
import sys
from shutil import rmtree, copytree
import logging
import json

from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.KBaseReportClient import KBaseReport
from installed_clients.GenericsAPIClient import GenericsAPI

from kb_RDP_Classifier.util.cli import run_check
from kb_RDP_Classifier.util.debug import dprint
from kb_RDP_Classifier.impl.globals import Var


##################################
##################################
testData_dir = '/kb/module/test/data'
##################################
##################################

####################################################################################################
################################ CI ################################################################
####################################################################################################
enigma50by30_noAttrMaps = '55136/4/1'
enigma50by30_noAttrMaps_tooShortSeqs = '55136/6/1'

enigma50by30 = '55136/15/1'
enigma50by30_rowAttrMap = '55136/11/1'

enigma17770by511 = '55136/26/1' # AmpliconMatrix
enigma17770by511_rowAttrMap = '55136/19/1'


userTest = '58225/2/1'

####################################################################################################
############################### appdev #############################################################
####################################################################################################



####################################################################################################
########################## dummy ###################################################################
####################################################################################################
dummy10by8_AmpMat_noRowAttrMap = 'dummy/10by8/AmpMat_noRowAttrMap'
dummy10by8_AmpMat_wRowAttrMap = 'dummy/10by8/AmpMat_wRowAttrMap'
dummy10by8_AttrMap = 'dummy/10by8/AttrMap'




def get_mock_gapi(dataset):
    mock_gapi = create_autospec(GenericsAPI, instance=True)

    def mock_gapi_fetch_sequence(params):
        logging.info('Mocking `gapi.fetch_sequence` with `params=%s`' % str(params))

        flpth = os.path.join(testData_dir, 'by_dataset_input', dataset, 'fetch_sequence/seqs.fna')
        return flpth

    mock_gapi.fetch_sequence.side_effect = mock_gapi_fetch_sequence

    return mock_gapi
        


def get_mock_dfu(dataset):
    '''
    Avoid lengthy `get_objects` and `save_objects`
    '''

    mock_dfu = create_autospec(DataFileUtil, instance=True)

    ##
    ## mock `save_objects` # TODO tease save and get apart
    def mock_dfu_save_objects(params):
        params_str = str(params)
        if len(params_str) > 100: params_str = params_str[:100] + ' ...'
        logging.info('Mocking `dfu.save_objects` with `params=%s`' % params_str)

        return [['mock', 1, 2, 3, 'dfu', 5, 'save_objects']] # UPA made from pos 6/0/4
    
    mock_dfu.save_objects.side_effect = mock_dfu_save_objects

    ##
    ## mock `get_objects`
    def mock_dfu_get_objects(params):
        logging.info('Mocking `dfu.get_objects` with `params=%s`' % str(params))

        upa = params['object_refs'][0].split(';')[-1]
        flnm = {
            enigma50by30_noAttrMaps: 'AmpliconMatrix.json',
            enigma50by30_noAttrMaps_tooShortSeqs: 'AmpliconMatrix.json',
            enigma50by30: 'AmpliconMatrix.json',
            enigma50by30_rowAttrMap: 'row_AttributeMapping.json',
            enigma17770by511: 'AmpliconMatrix.json',
            enigma17770by511_rowAttrMap: 'row_AttributeMapping.json',
            dummy10by8_AmpMat_wRowAttrMap: 'get_objects_AmpliconMatrix_wRowAttrMap.json',
            dummy10by8_AmpMat_noRowAttrMap: 'get_objects_AmpliconMatrix_noRowAttrMap.json',
            dummy10by8_AttrMap: 'get_objects_AttributeMapping.json',
            userTest: 'AmpliconMatrix.json',
            }[upa]
        flpth = os.path.join(testData_dir, 'by_dataset_input', dataset, 'get_objects', flnm)

        with open(flpth) as f:
            obj = json.load(f)

        return obj

    mock_dfu.get_objects.side_effect = mock_dfu_get_objects

    return mock_dfu


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
        src_drpth = os.path.join(testData_dir, 'by_dataset_input', dataset, ret_dir, 'RDP_Classifier_output')

        # check if it already exists
        # since app may create it before run, and
        # since `check_run` is called twice in this app
        if os.path.exists(Var.out_dir):
            rmtree(Var.out_dir)
        copytree(src_drpth, Var.out_dir)


    mock_run_check.side_effect = mock_run_check_

    return mock_run_check


def get_mock_kbr(dataset=None): 
    '''
    Avoid lengthy `create_extended_report`

    Does not use input currently
    '''

    mock_kbr = create_autospec(KBaseReport, instance=True) 

    # mock `create_extended_report`
    def mock_create_extended_report(params):
        logging.info('Mocking `kbr.create_extended_report`')

        return {
            'name': 'kbr_mock_name',
            'ref': 'kbr/mock/ref',
        }

    mock_kbr.create_extended_report.side_effect = mock_create_extended_report
    
    return mock_kbr




