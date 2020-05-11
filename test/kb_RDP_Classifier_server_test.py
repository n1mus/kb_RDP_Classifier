# -*- coding: utf-8 -*-
import os
import time
import unittest
from configparser import ConfigParser

from installed_clients.WorkspaceClient import Workspace

from kb_RDP_Classifier.kb_RDP_ClassifierImpl import kb_RDP_Classifier
from kb_RDP_Classifier.kb_RDP_ClassifierServer import MethodContext
from kb_RDP_Classifier.authclient import KBaseAuth as _KBaseAuth

from kb_RDP_Classifier.util import config
from kb_RDP_Classifier.util.config import _globals
from kb_RDP_Classifier.util.dprint import dprint, where_am_i
from kb_RDP_Classifier.util.error import *




params_debug = {
    'skip_obj': True,
    'skip_run': True,
    'return_testingInfo': True,
    'skip_objReport': True,
    }

params_rdp_classifier = {
    'conf': 0.51,
    'gene': '16srrna',
    'minWords': None,
    }


full17770 = "48255/26/3"
first50 = '48402/6/2'
secret_amp_set_upa = '49926/6/1' # no taxonomy or AttributeMappings


class kb_RDP_ClassifierTest(unittest.TestCase):
    '''
    Tests to run will be filtered by code block following class definition
    '''

    def test(self):
        ret = self.serviceImpl.classify(
            self.ctx, {
                **self.params_ws,
                'amplicon_set_upa': secret_amp_set_upa,
                'rdp_classifier': params_rdp_classifier,
                **params_debug,
            })

####################################################################################################
####################################################################################################
       
    def test_default_params(self):
        ret = self.serviceImpl.classify(
            self.ctx, {
                **self.params_ws,
                'amplicon_set_upa': first50,
            })

    def test_non_default_params(self):
        ret = self.serviceImpl.classify(
            self.ctx, {
                **self.params_ws,
                'amplicon_set_upa': first50,
                'output_name': 'an_output_name',
                'rdp_classifier': {
                    'conf': 0.222222222,
                    'gene': 'fungallsu',
                    'minWords': 5,
                    },
                'write_amplicon_set_taxonomy': 'overwrite',
                #-----------------------------------
                'return_testingInfo': True,
            })

    def test_params_validator(self):
        # TODO call a few times with invalid, assert ArgumentException or ValueError?
        pass

####################################################################################################
####################################################################################################
    '''
    Test behavior when no taxonomy uploaded or row AttributeMapping
    '''


    def test_no_taxonomy_or_AttributeMapping_doNotWrite(self):
        ret = self.serviceImpl.classify(
            self.ctx, {
                **self.params_ws,
                'amplicon_set_upa': secret_amp_set_upa,
                'write_amplicon_set_taxonomy': 'do_not_write',
                #-----------------------------------
                'return_testingInfo': True,
            })

    def test_no_taxonomy_or_AttributeMapping_doNotOverwrite(self):
        ret = self.serviceImpl.classify(
            self.ctx, {
                **self.params_ws,
                'amplicon_set_upa': secret_amp_set_upa,
                'write_amplicon_set_taxonomy': 'do_not_overwrite',
                #-----------------------------------
                'return_testingInfo': True,
            })
        
    def test_no_taxonomy_or_AttributeMapping_overwrite(self):
        ret = self.serviceImpl.classify(
            self.ctx, {
                **self.params_ws,
                'amplicon_set_upa': secret_amp_set_upa,
                'write_amplicon_set_taxonomy': 'overwrite',
                #-----------------------------------
                'return_testingInfo': True,
            })
        
####################################################################################################
    def test_attribute_already_exists(self):
        pass

####################################################################################################
    def test_large_data(self):
        pass

####################################################################################################
    def test_NonZeroReturnException(self):
        pass

    def test_ArgumentException(self):
        pass


####################################################################################################
   

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
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')
        test_names = [key for key, value in cls.__dict__.items() if type(key) == str and key.startswith('test') and callable(value)]
        print('All tests:', test_names)
        dec = '!!!' * 100
        print(dec,  "DO NOT FORGET TO GRAB HTML(S)", dec)


############################ filter what to run ####################################################
run_tests = ['test_default_params']

for key, value in kb_RDP_ClassifierTest.__dict__.copy().items():
    if type(key) == str and key.startswith('test') and callable(value):
        if key not in run_tests:
            delattr(kb_RDP_ClassifierTest, key)
