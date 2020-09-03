# -*- coding: utf-8 -*-
import os
import time
import unittest
from unittest.mock import patch
from configparser import ConfigParser
import json
import uuid

from installed_clients.WorkspaceClient import Workspace

from kb_RDP_Classifier.kb_RDP_ClassifierImpl import kb_RDP_Classifier
from kb_RDP_Classifier.kb_RDP_ClassifierServer import MethodContext
from kb_RDP_Classifier.authclient import KBaseAuth as _KBaseAuth

from kb_RDP_Classifier.util.config import Var
from kb_RDP_Classifier.util.params import flatten, Params
from kb_RDP_Classifier.util.kbase_obj import AmpliconSet, AmpliconMatrix, AttributeMapping
from kb_RDP_Classifier.util.dprint import dprint, where_am_i
from kb_RDP_Classifier.util.error import * # exceptions 
from kb_RDP_Classifier.kb_RDP_ClassifierImpl import run_check, parse_filterByConf, parse_shortSeq
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
        filterByConf_flpth = os.path.join(
            testData_dir, 'by_dataset_input/dummy_10by8/return/RDP_Classifier_output/out_filterByConf.tsv') 
        id2taxStr_d = parse_filterByConf(filterByConf_flpth)

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
        # TODO parameter validator

        ##
        ## test `flatten`

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

        flatd = flatten(d)

        self.assertTrue(len(flatd) == 7)
        self.assertTrue(all(['key%d' % i in flatd for i in range(7)]))
        self.assertTrue(all(['nest%d' % i not in flatd for i in range(2)]))
        self.assertTrue(flatd['key5'] == 'gnat')

        ##
        ## test `Params` defaults

        params = Params({
            'amplicon_set_upa': '1/2/3',
            'output_name': None,
            'rdp_clsf': {
                'conf': 0.8,
                'gene': '16srrna',
                'minWords': None,
            },
            'write_ampset_taxonomy': 'do_not_overwrite',
        })

        self.assertTrue(params['amplicon_set_upa'] == '1/2/3')
        self.assertTrue(params.getd('output_name') is None)
        self.assertTrue(params.getd('conf') == 0.8)
        self.assertTrue(params.getd('gene') == '16srrna')
        self.assertTrue(params.getd('minWords') is None)
        self.assertTrue(params.getd('write_ampset_taxonomy') == 'do_not_overwrite')

        self.assertTrue(
            params.prose_args == {
                'conf': '0.8',
                'gene': '16srrna',
                'minWords': 'default'
            },
            json.dumps(params.prose_args, indent=4)
        )
        self.assertTrue(params.cli_args == [])
        str(params) # should not throw

        ##
        ## test `Params` non-default

        params = Params({
            'amplicon_set_upa': '5/5/5',
            'output_name': 'my_ampset',
            'rdp_clsf': {
                'conf': 0.99999,
                'gene': 'fungallsu',
                'minWords': 100,
            },
            'write_ampset_taxonomy': 'overwrite',
        })

        self.assertTrue(params['amplicon_set_upa'] == '5/5/5')
        self.assertTrue(params.getd('output_name') == 'my_ampset')
        self.assertTrue(params.getd('conf') == 0.99999)
        self.assertTrue(params.getd('gene') == 'fungallsu')
        self.assertTrue(params.getd('minWords') == 100)
        self.assertTrue(params.getd('write_ampset_taxonomy') == 'overwrite')

        self.assertTrue(
            params.prose_args == {
                'conf': '0.99999',
                'gene': 'fungallsu',
                'minWords': '100'
            },
            json.dumps(params.prose_args, indent=4)
        )
        self.assertTrue(params.cli_args == ['--conf', '0.99999', '--gene', 'fungallsu', '--minWords', '100'], params.cli_args)
        str(params) # should not throw


        ##
        ## test `Params` no user-supplied values

        params = Params({
            'amplicon_set_upa': '6/6/6',
        })

        self.assertTrue(params['amplicon_set_upa'] == '6/6/6')
        self.assertTrue(params.getd('output_name') is None)
        self.assertTrue(params.getd('conf') == 0.8)
        self.assertTrue(params.getd('gene') == '16srrna')
        self.assertTrue(params.getd('minWords') is None)
        self.assertTrue(params.getd('write_ampset_taxonomy') == 'do_not_overwrite')

        self.assertTrue(
            params.prose_args == {
                'conf': '0.8',
                'gene': '16srrna',
                'minWords': 'default'
            },
            json.dumps(params.prose_args, indent=4)
        )
        self.assertTrue(params.cli_args == [])
        str(params) # should not throw

    ####################
    ####################
    @patch.dict('kb_RDP_Classifier.util.kbase_obj.Var', values={'dfu': get_mock_dfu('dummy_10by8'), 'warnings': []})
    def test_AmpliconSet(self):
        Var.run_dir = os.path.join(self.scratch, 'test_AmpliconSet_' + str(uuid.uuid4()))
        os.mkdir(Var.run_dir)

        ampset = AmpliconSet(dummy_10by8)
        
        ##
        ## test `to_fasta`

        fasta_flpth_test = os.path.join(Var.run_dir, 'study_seqs.fna')
        fasta_flpth_ref = os.path.join(testData_dir, 'by_dataset_input/dummy_10by8/return/study_seqs.fna')
        
        ampset.to_fasta(fasta_flpth_test)
        
        with open(fasta_flpth_test) as fh_test, open(fasta_flpth_ref) as fh_ref:
            self.assertTrue(fh_test.read().strip() == fh_ref.read().strip())

        ##
        ## test `write_taxonomy`

        filterByConf_flpth = os.path.join(
            testData_dir, 'by_dataset_input/dummy_10by8/return/RDP_Classifier_output/out_filterByConf.tsv') 
        id2taxStr_d = parse_filterByConf(filterByConf_flpth)

        # normal write
        ampset = AmpliconSet(dummy_10by8)
        ampset.write_taxonomy(id2taxStr_d, overwrite=False)
        self.assertTrue(Var.warnings == [])

        # normal write
        ampset = AmpliconSet(dummy_10by8)
        ampset.write_taxonomy(id2taxStr_d, overwrite=True)
        self.assertTrue(Var.warnings == [])

        # overwrite
        ampset = AmpliconSet(dummy_10by8)
        ampset.write_taxonomy(id2taxStr_d, overwrite=True)
        ampset.write_taxonomy(id2taxStr_d, overwrite=True)
        self.assertTrue(len(Var.warnings) == 1)
        self.assertTrue('`overwrite`' in Var.warnings[-1])
 
        # do not overwrite
        ampset = AmpliconSet(dummy_10by8)
        ampset.write_taxonomy(id2taxStr_d, overwrite=False)
        ampset.write_taxonomy(id2taxStr_d, overwrite=False)
        self.assertTrue(len(Var.warnings) == 2)
        self.assertTrue('`do_not_overwrite`' in Var.warnings[-1])
 
        # do not overwrite
        ampset = AmpliconSet(dummy_10by8)
        ampset.obj['amplicons']['amplicon_id_0']['taxonomy'] = {'fake': 'dummy'} 
        ampset.write_taxonomy(id2taxStr_d, overwrite=False)
        self.assertTrue(len(Var.warnings) == 3)
        self.assertTrue('`do_not_overwrite`' in Var.warnings[-1])
 


    ####################
    ####################
    @patch.dict('kb_RDP_Classifier.util.kbase_obj.Var', values={'dfu': get_mock_dfu('dummy_10by8'), 'warnings': []})
    def test_AmpliconMatrix_wRowAttrMap_AttributeMapping(self):
        '''
        Test row AttributeMapping behavior when AmpliconMatrix has row AttributeMapping
        '''

        amp_mat = AmpliconMatrix(dummy_10by8_AmpMat_wRowAttrMap)
        self.assertTrue(len(Var.warnings) == 0)

        attr_map = AttributeMapping(amp_mat.row_attrmap_upa, amp_mat)

        ##
        ## write new attribute/source
        ind_0 = attr_map.get_attribute_slot('biome', 'testing')
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
        ind_1 = attr_map.get_attribute_slot('celestial body', 'upload')
        self.assertTrue(ind_1 == 0)
        self.assertTrue(len(Var.warnings) == 1)

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
    @patch.dict('kb_RDP_Classifier.util.kbase_obj.Var', values={'dfu': get_mock_dfu('dummy_10by8'), 'warnings': []})
    def test_AmpliconMatrix_noRowAttrMap_AttributeMapping(self):
        '''
        Test row AttributeMapping behavior when AmpliconMatrix has now row AttributeMapping
        '''

        amp_mat = AmpliconMatrix(dummy_10by8_AmpMat_noRowAttrMap)
        attr_map = AttributeMapping(amp_mat.row_attrmap_upa, amp_mat)
        attr_map = AttributeMapping(amp_mat.row_attrmap_upa, amp_mat)

        self.assertTrue(len(Var.warnings) == 1, Var.warnings)

        ##
        ## write new attribute/source
        ind_0 = attr_map.get_attribute_slot('biome', 'testing')
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



    def test_report(self):
    ####################
    ####################
        # TODO
        pass

####################################################################################################
##################################### integration tests ############################################
####################################################################################################
    # TODO test params unique to your program
    # TODO overwrite, do_not_overwrite, do_not_write already enumerated in AmpliconSet unit test

    ####################
    ####################
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda u: get_mock_dfu('17770'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('17770'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda u: get_mock_kbr())
    def test(self):
        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amplicon_set_upa': _17770,
                'rdp_clsf': {
                    'conf': 0.51,
                    'gene': '16srrna',
                    'minWords': None,
                    },
            })     


    ####################
    ####################
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a: get_mock_dfu('17770'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('17770'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a: get_mock_kbr())
    def test_default_params(self):
        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amplicon_set_upa': _17770,
            })

    ####################
    ####################
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a: get_mock_dfu('17770'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('17770'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a: get_mock_kbr())
    def test_non_default_params(self):
        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amplicon_set_upa': _17770,
                'output_name': 'an_output_name',
                'rdp_clsf': {
                    'conf': 0.222222222,
                    'gene': 'fungallsu',
                    'minWords': 5,
                },
                'write_ampset_taxonomy': 'overwrite',
            })


    ####################
    ####################
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a: get_mock_dfu('secret'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('secret'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a: get_mock_kbr())
    def test_no_taxonomy_or_AttributeMapping_doNotWrite(self):
        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amplicon_set_upa': secret,
                'write_ampset_taxonomy': 'do_not_write',
            })

    ####################
    ####################
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a: get_mock_dfu('secret'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('secret'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a: get_mock_kbr())
    def test_no_taxonomy_or_AttributeMapping_doNotOverwrite(self):
        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amplicon_set_upa': secret,
                'write_ampset_taxonomy': 'do_not_overwrite',
            })
        
    ####################
    ####################
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a: get_mock_dfu('secret'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('secret'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a: get_mock_kbr())
    def test_no_taxonomy_or_AttributeMapping_overwrite(self):
        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amplicon_set_upa': secret,
                'write_ampset_taxonomy': 'overwrite',
            })
        

    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a: get_mock_dfu('SRS_OTU'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('SRS_OTU'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a: get_mock_kbr())
    ###################
    ###################
    def test_too_short_seq(self):
        ret =  self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amplicon_set_upa': SRS_OTU,
            })

    ####################
    ####################
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda u: get_mock_dfu('17770'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('17770', non_default_gene='silva_138_ssu'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda u: get_mock_kbr())
    def test_custom(self):
        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amplicon_set_upa': _17770,
                'rdp_clsf': {
                    'gene': 'silva_138_ssu',
                },
            })


#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    ####################
    ####################
    def test_assert(self):
        '''Test that asserts have not been compiled out'''
        with self.assertRaises(AssertionError):
            assert False

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
        tests = [key for key, value in cls.__dict__.items() if type(key) == str and key.startswith('test') and callable(value)]
        print('Tests ran:', tests)
        print('Tests skipped:', list(set(all_tests) - set(tests)))
        print('do_patch:', do_patch)
        dec = '!!!' * 200
        print(dec,  "DO NOT FORGET TO GRAB HTML(S)", dec)

    @staticmethod
    def subproc_run(cmd):
        logging.info('Running cmd: `%s`' % cmd)
        subprocess.run(cmd, shell=True, executable='/bin/bash', stdout=sys.stdout, stderr=sys.stderr)

    def shortDescription(self):
        '''Override unittest using test*() docstrings in lieu of test*() method name in output summary'''
        return None

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!! filter what to run !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
all_tests = [k for k, v in kb_RDP_ClassifierTest.__dict__.items() if k.startswith('test') and callable(v)]


unit_tests = [ # environment and patch-toggling independent
    'test_assert',
    'test_run_check', 'test_parse_filterByConf', 'test_params', 
    'test_AmpliconSet',
    'test_AmpliconMatrix_noRowAttrMap_AttributeMapping', 'test_AmpliconMatrix_wRowAttrMap_AttributeMapping',
    'test_report'
]
ci_tests = [ # integration tests
    'test',
    'test_default_params',
    'test_non_default_params',
    'test_no_taxonomy_or_AttributeMapping_overwrite',
    'test_no_taxonomy_or_AttributeMapping_doNotOverwrite',
    'test_no_taxonomy_or_AttributeMapping_doNotWrite',
    'test_custom',
]
appdev_tests = [ # integration tests
    'test_too_short_seq',
]

run_tests = ['test_custom']

for k, v in kb_RDP_ClassifierTest.__dict__.copy().items():
    if k.startswith('test') and callable(v):
        if k not in ci_tests:
            delattr(kb_RDP_ClassifierTest, k)
            pass
