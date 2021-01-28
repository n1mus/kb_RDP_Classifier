# -*- coding: utf-8 -*-
import os
import unittest
from unittest.mock import patch
import json
import uuid
import numpy as np
from pytest import raises

from kb_RDP_Classifier.util.debug import dprint, where_am_i
from kb_RDP_Classifier.impl.globals import Var
from kb_RDP_Classifier.impl.params import Params
from kb_RDP_Classifier.impl.kbase_obj import AmpliconMatrix, AttributeMapping
from kb_RDP_Classifier.impl import report
from data import *
from config import *


run_dir = os.path.join(scratch, 'test_report_' + str(uuid.uuid4()))
os.mkdir(run_dir)

req = dict(
    workspace_id='id',
    amp_mat_upa='u/p/a',
    output_name='out_name',
)

####################################################################################################
####################################################################################################
def test_large():
    '''
    Globals used:
    report_dir, report_template_flpth
    out_fixRank_flpth, out_filterByConf_flpth
    params
    '''

    Var.report_dir = os.path.join(run_dir, 'report_enigma17770by511')
    os.mkdir(Var.report_dir)
    out_dir = os.path.join(testData_dir, 'by_dataset_input/enigma17770by511/return/RDP_Classifier_output/')
    Var.out_fixRank_flpth = os.path.join(out_dir, 'out_fixRank.tsv')
    Var.out_filterByConf_flpth = os.path.join(out_dir, 'out_filterByConf.tsv')
    Var.params = Params(dict(
        **req,
        conf=0.7777
    ))

    html_links = report.HTMLReportWriter(
        cmd_l = ['test,', 'test,', 'large'] * 10
    ).write()


####################################################################################################
####################################################################################################
def test_small():
    
    out_dir = os.path.join(testData_dir, 'by_dataset_input/enigma50by30/return/RDP_Classifier_output')
    Var.out_fixRank_flpth = os.path.join(out_dir, 'out_fixRank.tsv')
    Var.out_filterByConf_flpth = os.path.join(out_dir, 'out_filterByConf.tsv')
    for i, conf in enumerate(np.linspace(0, 1, 11)):
        Var.report_dir = os.path.join(run_dir, 'report_enigma50by30_conf%g' % conf)
        os.mkdir(Var.report_dir)
        Var.params = Params(dict(
        **req,
            conf=conf
        ))

        html_links = report.HTMLReportWriter(
            cmd_l = ['test,', 'test,', 'small', 'conf=%g' % conf]
        ).write()


####################################################################################################
####################################################################################################
def test_dummy():
    out_dir = os.path.join(testData_dir, 'by_dataset_input/dummy10by8/return/RDP_Classifier_output')
    Var.out_fixRank_flpth = os.path.join(out_dir, 'out_fixRank.tsv')
    Var.out_filterByConf_flpth = os.path.join(out_dir, 'out_filterByConf.tsv')
    for i, conf in enumerate(np.linspace(0, 1, 11)):
        #if conf != 1: continue
        Var.report_dir = os.path.join(run_dir, 'report_dummy10by8_conf%g' % conf)
        os.mkdir(Var.report_dir)
        Var.params = Params(dict(
            **req,
            conf=conf,
        ))

        html_links = report.HTMLReportWriter(
            cmd_l = ['test,', 'test,', 'dummy10by8', 'conf=%g' % conf]
        ).write()

####################################################################################################
####################################################################################################
def test_tiny():
    out_dir = os.path.join(testData_dir, 'by_dataset_input/dummyTiny/return/RDP_Classifier_output')
    Var.out_filterByConf_flpth = os.path.join(out_dir, 'out_filterByConf.tsv')
    for i in range(5):
        Var.out_fixRank_flpth = os.path.join(out_dir, 'out_fixRank%d.tsv' % i)
        Var.report_dir = os.path.join(run_dir, 'report_dummyTiny_%d' % i)
        os.mkdir(Var.report_dir)
        Var.params = Params(dict(
            **req,
            conf=0.55555,
        ))

        with open(Var.out_fixRank_flpth) as fh:
            fixRank_lines = fh.readlines()

        html_links = report.HTMLReportWriter(
            cmd_l = ['test,', 'test,', 'dummyTiny', 'i=%d' % i] + fixRank_lines
        ).write()
               



