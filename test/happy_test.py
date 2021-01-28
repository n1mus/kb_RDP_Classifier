# -*- coding: utf-8 -*-
import os
import time
import unittest
from unittest.mock import patch
from configparser import ConfigParser
import json
import uuid
import numpy as np

from kb_RDP_Classifier.kb_RDP_ClassifierImpl import kb_RDP_Classifier
from kb_RDP_Classifier.util.debug import dprint, where_am_i
from kb_RDP_Classifier.impl.globals import Var
from kb_RDP_Classifier.impl.kbase_obj import AmpliconMatrix, AttributeMapping
from data import *
from config import patch_, patch_dict_
import config as cfg



class kb_RDP_ClassifierTest(cfg.BaseTest):
    '''
    Tests to run will be filtered by code block following class definition
    '''



    ####################
    ####################
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a: get_mock_dfu('enigma17770by511'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.GenericsAPI', new=lambda *a, **k: get_mock_gapi('enigma17770by511'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('enigma17770by511'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a: get_mock_kbr())
    def test_large(self):
        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amp_mat_upa': enigma17770by511,
                'output_name': 'out_name',
            })
        self._check_objects()   


    ####################
    ####################
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a: get_mock_dfu('enigma50by30'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.GenericsAPI', new=lambda *a, **k: get_mock_gapi('enigma50by30'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('enigma50by30'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a: get_mock_kbr())
    def test_default_params(self):
        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amp_mat_upa': enigma50by30,
                'output_name': 'out_name',
            })
        self._check_objects()

    ####################
    ####################
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a: get_mock_dfu('enigma50by30'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.GenericsAPI', new=lambda *a, **k: get_mock_gapi('enigma50by30'))
    #@patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('enigma50by30'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a: get_mock_kbr())
    def test_non_default_params(self):
        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amp_mat_upa': enigma50by30,
                'output_name': 'an_output_name',
                'rdp_clsf': {
                    'conf': 0.222222222,
                    'gene': 'fungallsu',
                    'minWords': 5,
                },
            })

        self._check_objects()

    ####################
    ####################
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a: get_mock_dfu('enigma50by30_noAttrMaps_noSampleSet'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.GenericsAPI', new=lambda *a, **k: get_mock_gapi('enigma50by30_noAttrMaps_noSampleSet'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('enigma50by30_noAttrMaps_noSampleSet'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a: get_mock_kbr())
    def test_no_row_AttributeMapping(self):
        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amp_mat_upa': enigma50by30_noAttrMaps_noSampleSet,
                'output_name': 'out_name',
                'rdp_clsf': {
                    'gene': '16srrna',
                },
            })
        self._check_objects()

        self.assertTrue(
            Var.params_report['objects_created'][0]['description'].startswith(
                'Created. Added attribute'
            )
        )



    ###################
    ###################
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a: get_mock_dfu('enigma50by30_noAttrMaps_noSampleSet_tooShortSeqs'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.GenericsAPI', new=lambda *a, **k: get_mock_gapi('enigma50by30_noAttrMaps_noSampleSet'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('enigma50by30_noAttrMaps_noSampleSet_tooShortSeqs'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a: get_mock_kbr())
    def test_too_short_seq(self):
        ret =  self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amp_mat_upa': enigma50by30_noAttrMaps_noSampleSet_tooShortSeqs,
                'output_name': 'out_name',
                'rdp_clsf': {
                    'gene': '16srrna',
                },
            })
        self._check_objects()


    ####################
    ####################
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda u: get_mock_dfu('enigma50by30_noAttrMaps_noSampleSet'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.GenericsAPI', new=lambda *a, **k: get_mock_gapi('enigma50by30_noAttrMaps_noSampleSet'))
    #@patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('enigma50by30_noAttrMaps_noSampleSet', non_default_gene='silva_138_ssu'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda u: get_mock_kbr())
    def test_custom(self):
        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amp_mat_upa': enigma50by30_noAttrMaps_noSampleSet,
                'output_name': 'out_name',
                'rdp_clsf': {
                    'gene': 'silva_138_ssu',
                },
            })
        self._check_objects()

    ####################
    ####################
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda u: get_mock_dfu('userTest'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.GenericsAPI', new=lambda *a, **k: get_mock_gapi('userTest'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('userTest', non_default_gene='silva_138_ssu'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda u: get_mock_kbr())
    def test_userTest_data(self):
        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amp_mat_upa': userTest,
                'output_name': 'out_name',
                'rdp_clsf': {
                    'gene': 'silva_138_ssu',
                },
            })
        self._check_objects()


    def _check_objects(self):
        self.assertTrue(Var.amp_mat.obj.get('row_attributemapping_ref') is not None)
        self.assertTrue(Var.amp_mat.obj.get('row_mapping') is not None)


#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


    @classmethod
    def list_tests(cls):
        return [key for key, value in cls.__dict__.items() if type(key) == str and key.startswith('test') and callable(value)]

    @classmethod
    def tearDownClass(cls):
        super(cls, cls).tearDownClass()

        skipped_tests = list(set(all_tests) - set(cls.list_tests()))
        print('* do_patch:', cfg.do_patch)
        print('* All tests (%d): %s' % (len(all_tests), all_tests))
        print('* Tests skipped (%d): %s' % (len(skipped_tests), skipped_tests))
        print('* Tests run (%d): %s' % (len(cls.list_tests()), cls.list_tests()))



#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!! filter what to run !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
all_tests = [k for k, v in kb_RDP_ClassifierTest.__dict__.items() if k.startswith('test') and callable(v)]


ci_tests = [ # integration tests
    'test_large',
    'test_default_params',
    'test_non_default_params',
    'test_no_row_AttributeMapping',
    'test_too_short_seq',
    'test_custom',
]


run_tests = ['test_userTest_data'] 
#run_tests = ['test_custom'] 
#run_tests = ['test_large'] 

for test in all_tests:
        if test not in run_tests:
            delattr(kb_RDP_ClassifierTest, test)
            pass
