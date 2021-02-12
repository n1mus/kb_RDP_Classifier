import os
import time
import unittest
from unittest.mock import patch
from configparser import ConfigParser
import json
import uuid

import pytest
import numpy as np

from installed_clients.WorkspaceClient import Workspace
from kb_RDP_Classifier.authclient import KBaseAuth as _KBaseAuth
from kb_RDP_Classifier.kb_RDP_ClassifierServer import MethodContext
from kb_RDP_Classifier.kb_RDP_ClassifierImpl import kb_RDP_Classifier



###################################### 
do_patch = True # toggle patching for tests that can run independently of it

if do_patch:
    patch_ = patch
    patch_dict_ = patch.dict
else:
    patch_ = lambda *a, **k: lambda f: f
    patch_dict_ = lambda *a, **k: lambda f: f
######################################
scratch = '/kb/module/work/tmp'
testData_dir = '/kb/module/test/data'
######################################
req = dict(
    workspace_id='id',
    amp_mat_upa='u/p/a',
    output_name='out_name',
)
######################################

class BaseTest(unittest.TestCase):

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

    def shortDescription(self):
        '''Override unittest using test*() docstrings in lieu of test*() method name in output summary'''
        return None



