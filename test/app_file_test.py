import os
from unittest.mock import patch
import json
import uuid

import numpy as np
from pytest import raises

from kb_RDP_Classifier.util.debug import dprint, where_am_i
from kb_RDP_Classifier.impl.globals import Var
from kb_RDP_Classifier.impl.kbase_obj import AmpliconMatrix, AttributeMapping
from kb_RDP_Classifier.impl.params import Params
from kb_RDP_Classifier.impl import app_file
from data import *
from config import req



def _add_dicts(*d_l):
    retd = {}
    for d in d_l:
        for k, v in d.items():
            if k in retd and retd[k] != v: raise Exception('Different values')
            retd[k] = v
    return retd



def test_get_fix_filtered_id2tax():
    '''
    Test: demangling, skipped ranks, filtered ranks
    '''
    Var.out_allRank_flpth = os.path.join(testData_dir, 'example_allRank.tsv') # old one without 'Genera Incertae Sedis'
    Var.params = Params({
        **req,
        'conf': 0.8
    })
    id2tax = app_file.get_fix_filtered_id2tax()

    id2tax_first = {
'000b0b88ceb19d19678f6c3a39f2db73': 'Bacteria;Proteobacteria;Alphaproteobacteria;Rhizobiales;Xanthobacteraceae;uncultured;',
'0013aacacdba8495d504237c6334ddfb': 'Bacteria;',
'00209e5d2aadb8c762613b92f7f4b21c': 'Bacteria;Verrucomicrobiota;Omnitrophia;Omnitrophales;Omnitrophaceae;Candidatus Omnitrophus;',
'0022fa9d411c3edb1b584d7fb5193749': 'Bacteria;Verrucomicrobiota;Verrucomicrobiae;Pedosphaerales;Pedosphaeraceae;',
'00250d6b968f2ad29019c64d89ece283': 'Bacteria;Proteobacteria;Gammaproteobacteria;Burkholderiales;Nitrosomonadaceae;MND1;',
'002597380ec40da68af2362f47542f89': '',
'0030f073f1f67fa8c7f01795583706e6': 'Bacteria;Proteobacteria;Gammaproteobacteria;Burkholderiales;Comamonadaceae;Rhodoferax;',
'0032ab5da12fadd744023dc9bbba5169': 'Bacteria;Proteobacteria;Gammaproteobacteria;Burkholderiales;',
'00360e9b675235e3ba5f1e6cf402cd73': 'Bacteria;Proteobacteria;Gammaproteobacteria;Burkholderiales;',
'0037cbd3eb6eaf9cba6a4c2b7d866d1f': 'Bacteria;Proteobacteria;Gammaproteobacteria;Diplorickettsiales;Diplorickettsiaceae;Aquicella;',
}
    id2tax_skipRanks = {
'0134a9074c4afc9ac763f0482578f9e5': 'Bacteria;Firmicutes;Limnochordia;;;Hydrogenispora;',
'18a980ed927822f60eebf93600ee8ff4': 'Bacteria;Acidobacteriota;Acidobacteriae;;;Paludibaculum;', 
'1a9c864d1f706bf185928fbf666f6880': 'Bacteria;Firmicutes;Clostridia;;Hungateiclostridiaceae;', 
'1d1f284b1a3fc4545be7430ae7365c91': 'Bacteria;Firmicutes;Desulfotomaculia;Desulfotomaculales;;Pelotomaculum;', 
'1ec12548cafe627d1212ffa9f9ef24c3': 'Bacteria;Acidobacteriota;Acidobacteriae;;;Paludibaculum;', 
'209d2a7b32e4fd9500896c1910760c01': 'Bacteria;Acidobacteriota;Acidobacteriae;;;Paludibaculum;', 
'22b3c70cdfb1714224e1bf8a6314bee9': 'Bacteria;Firmicutes;Clostridia;Peptostreptococcales-Tissierellales;;Finegoldia;', 
'24a0b0f872dcff5625c7e671b86607bc': 'Bacteria;Firmicutes;Clostridia;;Hungateiclostridiaceae;HN-HF0106;',
'faec42549c32f5c311164c00ff260f72': 'Bacteria;Acidobacteriota;Acidobacteriae;;;Paludibaculum;', 
'ff48ea2b9d30c737b53aeb9841179d57': 'Bacteria;Firmicutes;Clostridia;Peptostreptococcales-Tissierellales;;Parvimonas;',
}
    id2tax_demangle = {
'000b0b88ceb19d19678f6c3a39f2db73': 'Bacteria;Proteobacteria;Alphaproteobacteria;Rhizobiales;Xanthobacteraceae;uncultured;', 
'006344897e91aa92c15114a635558e4c': 'Bacteria;Firmicutes;Dethiobacteria;Dethiobacterales;Dethiobacteraceae;uncultured;', 
'0063886685aeb8abd4643ca43d63c6fd': 'Bacteria;Gemmatimonadota;Gemmatimonadetes;Gemmatimonadales;Gemmatimonadaceae;uncultured;', 
'00d4306620fb956f4cb8ea6616da13a3': 'Bacteria;Proteobacteria;Alphaproteobacteria;Rhizobiales;Rhizobiales Incertae Sedis;uncultured;', 
'010a64540ce2e484b2177289a377246b': 'Bacteria;Proteobacteria;Alphaproteobacteria;Rhizobiales;Xanthobacteraceae;uncultured;', 
'017740e814c004489ef488d9ba7e6bba': 'Bacteria;Chloroflexi;Anaerolineae;Anaerolineales;Anaerolineaceae;uncultured;', 
'018e02f503aa9297bdf4fa8a3a5caf0d': 'Bacteria;Spirochaetota;Spirochaetia;Spirochaetales;Spirochaetaceae;uncultured;', 
'019a8e93cde9dfce660c99097f2bc8ef': 'Bacteria;Proteobacteria;Alphaproteobacteria;Reyranellales;Reyranellaceae;uncultured;',    
'ffdb83232218318beacfa5b9d2802d23': 'Bacteria;Gemmatimonadota;Gemmatimonadetes;Gemmatimonadales;Gemmatimonadaceae;uncultured;', 
'ffe9568c3bbd5838f866595074ba1148': 'Bacteria;Desulfobacterota;Desulfuromonadia;Geobacterales;Geobacteraceae;uncultured;',
}
    id2tax_expected = _add_dicts(
        id2tax_first,
        id2tax_skipRanks,
        id2tax_demangle,
    )

    dprint('len(id2tax_expected) # should be about 30')

    for id in id2tax_expected.keys():
        assert id2tax[id] == id2tax_expected[id], '%s:\n%s\n%s' % (id, id2tax[id], id2tax_expected[id])



def test_parse_shortSeq():
    pass


