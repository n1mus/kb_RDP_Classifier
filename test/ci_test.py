# -*- coding: utf-8 -*-
import os
import time
import unittest
from unittest.mock import patch
from configparser import ConfigParser
import json
import uuid
import numpy as np

from installed_clients.WorkspaceClient import Workspace
from kb_RDP_Classifier.kb_RDP_ClassifierServer import MethodContext
from kb_RDP_Classifier.authclient import KBaseAuth as _KBaseAuth

from kb_RDP_Classifier.kb_RDP_ClassifierImpl import kb_RDP_Classifier
from kb_RDP_Classifier.util.debug import dprint, where_am_i
from kb_RDP_Classifier.util.cli import run_check, NonZeroReturnException
from kb_RDP_Classifier.impl.params import Params
from kb_RDP_Classifier.impl.globals import Var
from kb_RDP_Classifier.impl.kbase_obj import AmpliconMatrix, AttributeMapping
from kb_RDP_Classifier.impl.comm import * # exceptions 
from kb_RDP_Classifier.impl import app_file
from kb_RDP_Classifier.impl import report
from mocks import * # upas, mocks ...

######################################
######################################
######### TOGGLE PATCH ###############
######################################
###################################### 
do_patch = True # toggle patching for tests that can run independently of it

if do_patch:
    patch_ = patch
    patch_dict_ = patch.dict
else:
    patch_ = lambda *a, **k: lambda f: f
    patch_dict_ = lambda *a, **k: lambda f: f
######################################
######################################
######################################
######################################


class kb_RDP_ClassifierTest(unittest.TestCase):
    '''
    Tests to run will be filtered by code block following class definition
    '''

    def _check_objects(self):
        self.assertTrue(Var.amp_mat.obj.get('row_attributemapping_ref') is not None)
        self.assertTrue(Var.amp_mat.obj.get('row_mapping') is not None)


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


    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a: get_mock_dfu('enigma50by30_noAttrMaps_noSampleSet_tooShortSeqs'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.GenericsAPI', new=lambda *a, **k: get_mock_gapi('enigma50by30_noAttrMaps_noSampleSet'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('enigma50by30_noAttrMaps_noSampleSet_tooShortSeqs'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a: get_mock_kbr())
    ###################
    ###################
    def test_too_short_seq(self):
        ret =  self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amp_mat_upa': enigma50by30_noAttrMaps_noSampleSet_tooShortSeqs,
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
                'rdp_clsf': {
                    'gene': 'silva_138_ssu',
                },
            })
        self._check_objects()

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    @classmethod
    def setUpClass(cls):
        token = os.environ.get('KB_AUTH_TOKEN', None)
        config_file = os.environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('kb_RDP_Classifier'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'kb_RDP_Classifier',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = Workspace(cls.wsURL)
        suffix = int(time.time() * 1000)
        cls.wsName = "kb_RDP_Classifier_" + str(suffix)
        cls.wsId = cls.wsClient.create_workspace({'workspace': cls.wsName})[0]                      
        cls.params_ws = {                                                                           
            'workspace_id': cls.wsId,                                                               
            'workspace_name': cls.wsName,                                                           
        } 
        cls.serviceImpl = kb_RDP_Classifier(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']

    @classmethod
    def list_tests(cls):
        return [key for key, value in cls.__dict__.items() if type(key) == str and key.startswith('test') and callable(value)]

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')
        dec = '!!!' * 200
        print(dec,  "DO NOT FORGET TO GRAB HTML(S)", dec)

        skipped_tests = list(set(all_tests) - set(cls.list_tests()))
        print('* do_patch:', do_patch)
        print('* All tests (%d): %s' % (len(all_tests), all_tests))
        print('* Tests skipped (%d): %s' % (len(skipped_tests), skipped_tests))
        print('* Tests run (%d): %s' % (len(cls.list_tests()), cls.list_tests()))

    def shortDescription(self):
        '''Override unittest using test*() docstrings in lieu of test*() method name in output summary'''
        return None

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
appdev_tests = [ # integration tests
]

run_tests = ['test_no_row_AttributeMapping'] 
#run_tests = ['test_custom'] 
#run_tests = ['test_large'] 

for test in all_tests:
        if test not in run_tests:
            #delattr(kb_RDP_ClassifierTest, test)
            pass
