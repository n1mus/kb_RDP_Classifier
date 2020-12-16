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
from kb_RDP_Classifier.impl.error import * # exceptions 
from kb_RDP_Classifier.impl import app_file
from kb_RDP_Classifier.impl.report import HTMLReportWriter
from mocks import * # upas, mocks ...

######################################
######################################
######### TOGGLE PATCH ###############
######################################
###################################### 
do_patch = False # toggle patching for tests that can run independently of it

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
####################################################################################################
############################# UNIT TESTS ###########################################################
####################################################################################################

    ####################
    ####################
    def test_run_check(self):
        '''
        Test `run_check` which runs executable
        ''' 

        with self.assertRaises(NonZeroReturnException) as cm:
            run_check('set -o pipefail && ;s |& tee tmp')
            self.assertTrue('`2`') in str(cm.exception) # return code 2

        with self.assertRaises(NonZeroReturnException) as cm:
            run_check('set -o pipefail && tmp |& tee tmp')
            self.assertTrue('`127`') in str(cm.exception) # return code 127

        with self.assertRaises(NonZeroReturnException) as cm:
            run_check('set -o pipefail && echo hi |& tmp')
            self.assertTrue('`127`') in str(cm.exception) # return code 127

        run_check('set -o pipefail && echo hi |& tee tmp') # run correctly


    ####################
    ####################
    def test_parse_filterByConf(self):
        Var.out_filterByConf_flpth = os.path.join(
            testData_dir, 'by_dataset_input/dummy10by8/return/RDP_Classifier_output/out_filterByConf.tsv') 
        id2taxStr_d = app_file.parse_filterByConf()

        self.assertTrue(len(id2taxStr_d) == 10)
        self.assertTrue(all(['amplicon_id_%d' % i in id2taxStr_d for i in range(10)]))
        self.assertTrue(all([taxStr.count(';') == 6 for taxStr in id2taxStr_d.values()]))

        self.assertTrue(id2taxStr_d['amplicon_id_0'] == 
            'Bacteria;Proteobacteria;Alphaproteobacteria;Rhizobiales;unclassified_Rhizobiales;unclassified_Rhizobiales;')
        self.assertTrue(id2taxStr_d['amplicon_id_9'] == 
            'Bacteria;Proteobacteria;Gammaproteobacteria;Legionellales;Coxiellaceae;Aquicella;')

    ####################
    ####################
    def test_parse_shortSeq(self):
        # TODO
        pass

    ####################
    ####################
    def test_params(self):

        ##
        ## test `Params._validate` which mostly spots misspelled parameters
        p = dict(
            workspace_id=None,
            workspace_name=None,
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
            workspace_name=None,
            amp_mat_upa=None,
            rdp_clsf=dict(
                gene=None,
                conf=None,
            ),
            outptu_name=None,
        )
        with self.assertRaises(Exception): Params(p)


        ##
        ## test `Params.flatten`

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

        self.assertTrue(len(flatd) == 7)
        self.assertTrue(all(['key%d' % i in flatd for i in range(7)]))
        self.assertTrue(all(['nest%d' % i not in flatd for i in range(2)]))
        self.assertTrue(flatd['key5'] == 'gnat')

        ##
        ## test `Params` defaults
        with self.subTest('defaults'):

            params = Params({
                'amp_mat_upa': '1/2/3',
                'output_name': None,
                'rdp_clsf': {
                    'conf': 0.8,
                    'gene': 'silva_138_ssu',
                    'minWords': None,
                },
            })

            self.assertTrue(params['amp_mat_upa'] == '1/2/3')
            self.assertTrue(params.getd('output_name') is None)
            self.assertTrue(params.getd('conf') == 0.8)
            self.assertTrue(params.getd('gene') == 'silva_138_ssu')
            self.assertTrue(params.getd('minWords') is None)

            self.assertTrue(
                params.prose_args == {
                    'conf': '0.8',
                    'gene': 'silva_138_ssu',
                    'minWords': 'default'
                },
                json.dumps(params.prose_args, indent=4)
            )
            self.assertTrue(params.cli_args == [
                    '--train_propfile', 
                    '/kb/module/data/SILVA_138_SSU_NR_99/rRNAClassifier.properties'
                ],
                params.cli_args
            )
            str(params) # should not throw

        ##
        ## test `Params` non-default
        with self.subTest('non-default'):

            params = Params({
                'amp_mat_upa': '5/5/5',
                'output_name': 'my_ampset',
                'rdp_clsf': {
                    'conf': 0.99999,
                    'gene': 'fungallsu',
                    'minWords': 100,
                },
            })

            self.assertTrue(params['amp_mat_upa'] == '5/5/5')
            self.assertTrue(params.getd('output_name') == 'my_ampset')
            self.assertTrue(params.getd('conf') == 0.99999)
            self.assertTrue(params.getd('gene') == 'fungallsu')
            self.assertTrue(params.getd('minWords') == 100)

            self.assertTrue(
                params.prose_args == {
                    'conf': '0.99999',
                    'gene': 'fungallsu',
                    'minWords': '100'
                },
                json.dumps(params.prose_args, indent=4)
            )
            self.assertTrue(
                params.cli_args == [
                    '--conf', '0.99999', '--gene', 'fungallsu', '--minWords', '100'
                ], 
                params.cli_args
            )
            str(params) # should not throw


        ##
        ## test `Params` no user-supplied values
        with self.subTest('no user-supplied values'):

            params = Params({
                'amp_mat_upa': '6/6/6',
            })

            self.assertTrue(params['amp_mat_upa'] == '6/6/6')
            self.assertTrue(params.getd('output_name') is None)
            self.assertTrue(params.getd('conf') == 0.8)
            self.assertTrue(params.getd('gene') == 'silva_138_ssu')
            self.assertTrue(params.getd('minWords') is None)

            self.assertTrue(
                params.prose_args == {
                    'conf': '0.8',
                    'gene': 'silva_138_ssu',
                    'minWords': 'default'
                },
                json.dumps(params.prose_args, indent=4)
            )
            self.assertTrue(params.cli_args == [
                '--train_propfile', 
                '/kb/module/data/SILVA_138_SSU_NR_99/rRNAClassifier.properties'
                ],
                params.cli_args
            )
            str(params) # should not throw



    ####################
    ####################
    @patch.dict('kb_RDP_Classifier.impl.kbase_obj.Var', values={'dfu': get_mock_dfu('dummy10by8'), 'warnings': []})
    def test_AmpliconMatrix_wRowAttrMap_AttributeMapping(self):
        '''
        Test row AttributeMapping behavior when AmpliconMatrix has row AttributeMapping
        Row AttributeMapping indices should be in sync with AmpliconMatrix indices (1 to 1)
        '''
        Var.run_dir = os.path.join(
            self.scratch, 
            'test_AmpliconMatix_wRowAttributeMapping_AttributeMapping_' + str(uuid.uuid4())
        )

        amp_mat = AmpliconMatrix(dummy10by8_AmpMat_wRowAttrMap)
        self.assertTrue(len(Var.warnings) == 0)

        attr_map = AttributeMapping(amp_mat.obj.get('row_attributemapping_ref'), amp_mat)

        ##
        ## write new attribute/source
        ind_0 = attr_map.get_attribute_slot_warn('biome', 'testing')
        self.assertTrue(ind_0 == 2)
        self.assertTrue(len(Var.warnings) == 0)

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

        self.assertTrue(attr_map.obj['instances']['amplicon_id_4'][ind_0] == 'dummy0')

        ##
        ## overwrite attribute/source
        nwarn0 = len(Var.warnings)
        ind_1 = attr_map.get_attribute_slot_warn('celestial body', 'upload')
        self.assertTrue(ind_1 == 0)
        self.assertTrue(len(Var.warnings) - nwarn0 == 1, json.dumps(attr_map.obj, indent=3))

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
            self.assertTrue(len(attr_l) == num_attr)

        ## 
        ## check did not add dummy attribute to wrong slot
        ind_lftvr = list(set(range(num_attr)) - {ind_0, ind_1})

        for attr_l in attr_map.obj['instances']:
            for ind in ind_lftvr:
                self.assertTrue('dummy' not in attr_l[ind])

 
    ####################
    ####################
    @patch.dict('kb_RDP_Classifier.impl.kbase_obj.Var', values={'dfu': get_mock_dfu('dummy10by8'), 'warnings': ['start']})
    def test_AmpliconMatrix_noRowAttrMap_AttributeMapping(self):
        '''
        Test row AttributeMapping behavior when AmpliconMatrix has now row AttributeMapping
        '''
        Var.run_dir = os.path.join(
            self.scratch, 
            'test_AmpliconMatix_noRowAttributeMapping_AttributeMapping_' + str(uuid.uuid4())
        )

        amp_mat = AmpliconMatrix(dummy10by8_AmpMat_noRowAttrMap)
        attr_map = AttributeMapping(amp_mat.obj.get('row_attributemapping_ref'), amp_mat)

        self.assertTrue(len(Var.warnings) == 1, Var.warnings)

        ##
        ## write new attribute/source
        ind_0 = attr_map.get_attribute_slot_warn('biome', 'testing')
        self.assertTrue(ind_0 == 0)
        self.assertTrue(len(Var.warnings) == 1)

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

        self.assertTrue(attr_map.obj['instances']['amplicon_id_4'][ind_0] == 'dummy0')

        ##
        ## all same length
        num_attr = len(attr_map.obj['attributes'])
        for attr_l in attr_map.obj['instances'].values():
            self.assertTrue(len(attr_l) == num_attr)



    ####################
    ####################
    def test_report(self):
        '''
        Globals used:
        report_dir, report_template_flpth
        out_fixRank_flpth, out_filterByConf_flpth
        params
        '''
        run_dir = os.path.join(self.scratch, 'test_report_' + str(uuid.uuid4()))
        os.mkdir(run_dir)

        ## Large Report
        Var.report_dir = os.path.join(run_dir, 'report_enigma17770by511')
        os.mkdir(Var.report_dir)
        out_dir = os.path.join(testData_dir, 'by_dataset_input/enigma17770by511/return/RDP_Classifier_output/')
        Var.out_fixRank_flpth = os.path.join(out_dir, 'out_fixRank.tsv')
        Var.out_filterByConf_flpth = os.path.join(out_dir, 'out_filterByConf.tsv')
        Var.params = Params(dict(
            conf=0.8111
        ))

        html_links = HTMLReportWriter(
            cmd_l = ['test,', 'test,', 'large']
        ).write()

        ## Small Reports
        out_dir = os.path.join(testData_dir, 'by_dataset_input/enigma50by30/return/RDP_Classifier_output')
        Var.out_fixRank_flpth = os.path.join(out_dir, 'out_fixRank.tsv')
        Var.out_filterByConf_flpth = os.path.join(out_dir, 'out_filterByConf.tsv')
        for i, conf in enumerate(np.linspace(0, 1, 11)):
            Var.report_dir = os.path.join(run_dir, 'report_enigma50by30_conf%g' % conf)
            os.mkdir(Var.report_dir)
            Var.params = Params(dict(
                conf=conf
            ))

            html_links = HTMLReportWriter(
                cmd_l = ['test,', 'test,', 'small', 'conf=%g' % conf]
            ).write()

        ## Dummy Reports
        out_dir = os.path.join(testData_dir, 'by_dataset_input/dummy10by8/return/RDP_Classifier_output')
        Var.out_fixRank_flpth = os.path.join(out_dir, 'out_fixRank.tsv')
        Var.out_filterByConf_flpth = os.path.join(out_dir, 'out_filterByConf.tsv')
        for i, conf in enumerate(np.linspace(0, 1, 11)):
            #if conf != 1: continue
            Var.report_dir = os.path.join(run_dir, 'report_dummy10by8_conf%g' % conf)
            os.mkdir(Var.report_dir)
            Var.params = Params(dict(
                conf=conf,
            ))

            html_links = HTMLReportWriter(
                cmd_l = ['test,', 'test,', 'dummy', 'conf=%g' % conf]
            ).write()

        ## Small Pie





####################################################################################################
##################################### integration tests ############################################
####################################################################################################

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


unit_tests = [ # environment and patch-toggling independent
    'test_run_check', 'test_params', 
     'test_parse_filterByConf', 'test_parse_shortSeq',
    'test_AmpliconMatrix_noRowAttrMap_AttributeMapping', 'test_AmpliconMatrix_wRowAttrMap_AttributeMapping',
    'test_report',
]
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

run_tests = ['test_default_params'] 

for test in all_tests:
        if test not in run_tests:
            delattr(kb_RDP_ClassifierTest, test)
            pass
