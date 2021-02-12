from unittest.mock import patch

import numpy as np
import pandas as pd

from kb_RDP_Classifier.util.debug import dprint
from kb_RDP_Classifier.impl.ana import (
    hist_0_1_10,
    TaxTree,
    get_rank2confs,
    get_cutoff_rank_counts
)


def test_TaxTree():
    pass


def test_get_rank2confs():
    df_fixRank = pd.DataFrame(
        [
            ['D', 0.9, 'P', 0.8, 'C', 0.7, 'O', 0.6, 'F', 0.5, 'G', 0.4],
            ['D', 0.9, 'P', 0.8, 'C', 0.7, 'O', 0.6, 'F', 0.5, np.nan, np.nan],
            ['D', 0.9, 'P', 0.8, np.nan, np.nan, 'O', 0.6, np.nan, np.nan, np.nan, np.nan],
        ],
        columns=[
            'domain', 'domain_conf', 
            'phylum', 'phylum_conf', 
            'class', 'class_conf', 
            'order', 'order_conf', 
            'family', 'family_conf', 
            'genus', 'genus_conf',
        ],
        index=list('abc'),
    )

    rank2confs = {
        'domain': [0.9,0.9,0.9], 
        'phylum': [0.8,0.8,0.8], 
        'class':  [0.7,0.7], 
        'order':  [0.6,0.6,0.6], 
        'family': [0.5,0.5], 
        'genus':  [0.4],
    }

    with patch('kb_RDP_Classifier.impl.app_file.get_fixRank', new=lambda: df_fixRank):
        assert get_rank2confs() == rank2confs, \
            '%s vs %s' % (get_rank2confs, rank2confs)


def test_get_cutoff_rank_counts():
    id2tax = {
        0: '',
        1: ';',
        2: ';;',
        3: ';;;',
        4: ';;;;',
        5: ';;;;;',
        6: ';;;;;;',
    }

    counts = {
        'root': 1,
        'domain': 1, 
        'phylum': 1, 
        'class': 1, 
        'order': 1, 
        'family': 1, 
        'genus': 1,
    }
    
    with patch('kb_RDP_Classifier.impl.app_file.get_fix_filtered_id2tax', new=lambda: id2tax):
        assert get_cutoff_rank_counts() == counts, \
            '%s vs %s' % (get_cutoff_rank_counts(), counts)


def test_hist_0_1_10():
    expected = [
        (
            [],
            [0,0,0,0,0,0,0,0,0,0],
        ), (
            [0,0,0],
            [3,0,0,0,0,0,0,0,0,0],
        ), (
            [0.5,0.55,0.22],
            [0,0,1,0,0,2,0,0,0,0],
        ), (
            [0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0],
            [1,1,1,1,1,1,1,1,1,2],
        ), (
            [0,0.1,0.9,1],
            [1,1,0,0,0,0,0,0,0,2],
        ), (
            [-0.1,1.1],
            [0,0,0,0,0,0,0,0,0,0],
        )

    ]

    for q, e in expected:
        r = hist_0_1_10(q) 
        assert np.all(r == e), \
            '%s vs %s' % (hist_0_1_10(q), e)
        #dprint(
        #    'q',
        #    'hist_0_1_10(q)',
        #    'np.array(e)',
        #    'len(e)',
        #)




