import os
from unittest.mock import patch
import json
import uuid
import numpy as np
from pytest import raises

from kb_RDP_Classifier.util.debug import dprint, where_am_i
from kb_RDP_Classifier.impl.globals import Var
from kb_RDP_Classifier.impl.kbase_obj import AmpliconMatrix, AttributeMapping
from kb_RDP_Classifier.impl import app_file
from data import *
from config import *



####################
####################
def test_parse_filterByConf():
    Var.out_filterByConf_flpth = os.path.join(
        testData_dir, 'by_dataset_input/dummy10by8/return/RDP_Classifier_output/out_filterByConf.tsv') 
    id2taxStr_d = app_file.parse_filterByConf()

    assert len(id2taxStr_d) == 10
    assert all(['amplicon_id_%d' % i in id2taxStr_d for i in range(10)])
    assert all([taxStr.count(';') == 6 for taxStr in id2taxStr_d.values()])

    assert(id2taxStr_d['amplicon_id_0'] == 
        'Bacteria;Proteobacteria;Alphaproteobacteria;Rhizobiales;unclassified_Rhizobiales;unclassified_Rhizobiales;')
    assert(id2taxStr_d['amplicon_id_9'] == 
        'Bacteria;Proteobacteria;Gammaproteobacteria;Legionellales;Coxiellaceae;Aquicella;')

####################
####################
def test_parse_shortSeq():
    # TODO
    pass


