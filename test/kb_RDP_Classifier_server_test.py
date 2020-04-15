# -*- coding: utf-8 -*-
import os
import time
import unittest
from configparser import ConfigParser

from installed_clients.WorkspaceClient import Workspace

from kb_RDP_Classifier.kb_RDP_ClassifierImpl import kb_RDP_Classifier
from kb_RDP_Classifier.kb_RDP_ClassifierServer import MethodContext
from kb_RDP_Classifier.authclient import KBaseAuth as _KBaseAuth

from kb_RDP_Classifier.util import config # test turn off debug
from kb_RDP_Classifier.util.config import _globals
from kb_RDP_Classifier.util.dprint import dprint, where_am_i
from kb_RDP_Classifier.util.error import *




params_debug = {
    #'skip_run': True,
    'mini_data': True,
    'skip_save_obj': True,
    'skip_save_retFiles': True,
    }

params_rdp_classifier = {
    'conf': 0.5,
    'gene': '16srrna',
    'minWords': None,
    }


enigma_amp_set_upa = "48255/26/3"
enigmaFirst50_amp_set_upa = '48402/6/2'


class kb_RDP_ClassifierTest(unittest.TestCase):

    def test(self):
        ret = self.serviceImpl.classify(
            self.ctx, {
                **self.params_ws,
                #**params_debug,
                'amplicon_set_upa': enigma_amp_set_upa,
                'output_name': 'an_output_name',
                **params_rdp_classifier,
                }
            )

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

