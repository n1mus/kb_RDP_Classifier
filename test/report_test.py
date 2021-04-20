# -*- coding: utf-8 -*-
import os
import unittest
from unittest.mock import patch
import json
import uuid

import numpy as np
import pytest
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
def test_small():
    
    out_dir = os.path.join(TEST_DATA_DIR, 'return/enigma50by30/return/RDP_Classifier_output')
    Var.out_allRank_flpth = os.path.join(out_dir, 'out_allRank.tsv')
    Var.report_dir = os.path.join(run_dir, 'report_enigma50by30')
    os.mkdir(Var.report_dir)
    Var.params = Params(dict(
    **req,
        conf=0.8
    ))

    html_links = report.HTMLReportWriter(
        cmd_l = ['test,', 'test,', 'small']
    ).write()   

####################################################################################################
####################################################################################################
def test_small_linspace():
    
    out_dir = os.path.join(TEST_DATA_DIR, 'return/enigma50by30/return/RDP_Classifier_output')
    Var.out_allRank_flpth = os.path.join(out_dir, 'out_allRank.tsv')
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
@pytest.mark.parametrize('i,conf', list(enumerate(np.linspace(0, 1, 11))))
def test_dummy(i, conf):
    out_dir = os.path.join(TEST_DATA_DIR, 'return/dummy10by8/return/RDP_Classifier_output')
    Var.out_allRank_flpth = os.path.join(out_dir, 'out_allRank.tsv')
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
@pytest.mark.parametrize('i', list(range(5)))
def test_tiny(i):
    out_dir = os.path.join(TEST_DATA_DIR, 'return/dummyTiny/return/RDP_Classifier_output')
    Var.out_allRank_flpth = os.path.join(out_dir, 'out_allRank%d.tsv' % i)
    Var.report_dir = os.path.join(run_dir, 'report_dummyTiny_%d' % i)
    os.mkdir(Var.report_dir)
    Var.params = Params(dict(
        **req,
        conf=0.55555,
    ))

    with open(Var.out_allRank_flpth) as fh:
        allRank_lines = fh.readlines()

    html_links = report.HTMLReportWriter(
        cmd_l = ['test,', 'test,', 'dummyTiny', 'i=%d' % i] + allRank_lines
    ).write()
               



