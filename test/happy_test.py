# -*- coding: utf-8 -*-
import os
import time
import unittest
from unittest.mock import patch
from configparser import ConfigParser
import json
import uuid

import numpy as np
import pytest

from kb_RDP_Classifier.kb_RDP_ClassifierImpl import kb_RDP_Classifier
from kb_RDP_Classifier.util.debug import dprint, where_am_i
from kb_RDP_Classifier.impl.globals import Var
from kb_RDP_Classifier.impl.kbase_obj import AmpliconMatrix, AttributeMapping
from data import *
from config import patch_, patch_dict_
import config as cfg



class Test(cfg.BaseTest):

    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a, **k: mock_dfu)
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.GenericsAPI', new=lambda *a, **k: mock_gapi)
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('enigma50by30'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a, **k: mock_kbr)
    def test_default_params(self):
        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amp_mat_upa': enigma50by30,
                'output_name': 'out_name',
            })
        self._check_objects()

    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a, **k: mock_dfu)
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.GenericsAPI', new=lambda *a, **k: mock_gapi)
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('enigma50by30', non_default_gene='fungallsu'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a, **k: mock_kbr)
    def test_non_default_params(self):
        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amp_mat_upa': enigma50by30,
                'output_name': 'an_output_name',
                'rdp_clsf': {
                    'conf': 0.222222222,
                    'gene': 'fungallsu',
                },
            })

        self._check_objects()

    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a, **k: mock_dfu)
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.GenericsAPI', new=lambda *a, **k: mock_gapi)
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('enigma50by30_noAttrMaps'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a, **k: mock_kbr)
    def test_no_row_AttributeMapping(self):
        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amp_mat_upa': enigma50by30_noAttrMaps,
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

    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a, **k: mock_dfu)
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.GenericsAPI', new=lambda *a, **k: mock_gapi)
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('enigma50by30_noAttrMaps_tooShortSeqs'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a, **k: mock_kbr)
    def test_too_short_seq(self):
        ret =  self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amp_mat_upa': enigma50by30_noAttrMaps_tooShortSeqs,
                'output_name': 'out_name',
                'rdp_clsf': {
                    'gene': '16srrna',
                },
            })
        self._check_objects()


    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a, **k: mock_dfu)
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.GenericsAPI', new=lambda *a, **k: mock_gapi)
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a, **k: mock_kbr)
    def test_custom_small(self):
        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amp_mat_upa': enigma50by30,
                'output_name': 'out_name',
                'rdp_clsf': {
                    'gene': 'silva_138_ssu',
                },
            })
        self._check_objects()

        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amp_mat_upa': enigma50by30,
                'output_name': 'out_name',
                'rdp_clsf': {
                    'gene': 'silva_138_ssu_v4',
                },
            })
        self._check_objects()


    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a, **k: mock_dfu)
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.GenericsAPI', new=lambda *a, **k: mock_gapi)
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('userTest', non_default_gene='silva_138_ssu'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a, **k: mock_kbr)
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


    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.DataFileUtil', new=lambda *a, **k: mock_dfu)
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.GenericsAPI', new=lambda *a, **k: mock_gapi)
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.run_check', new=get_mock_run_check('ANL_amp'))
    @patch_('kb_RDP_Classifier.kb_RDP_ClassifierImpl.KBaseReport', new=lambda *a, **k: mock_kbr)
    def test_ANL_amp(self):
        with pytest.raises(Exception, match='No sequences were long enough'):
            ret = self.serviceImpl.run_classify(
                self.ctx, {
                    **self.params_ws,
                    'amp_mat_upa': ANL_amp,
                    'output_name': 'out_name',
                    'rdp_clsf': {
                        'gene': 'silva_138_ssu',
                    },
                })

    @unittest.skip('private, long')
    def test_large(self):
        ret = self.serviceImpl.run_classify(
            self.ctx, {
                **self.params_ws,
                'amp_mat_upa': enigma17770by511,
                'output_name': 'out_name',
            })
        self._check_objects()   

    def _check_objects(self):
        self.assertTrue(Var.amp_mat.obj.get('row_attributemapping_ref') is not None)
        self.assertTrue(Var.amp_mat.obj.get('row_mapping') is not None)



