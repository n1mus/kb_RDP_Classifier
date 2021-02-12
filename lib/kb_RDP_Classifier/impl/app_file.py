'''
For parsing or otherwise manipulating app input and output files
'''
import os
import re
from functools import lru_cache

import numpy as np
import pandas as pd

from ..util.debug import dprint, TimePartition
from ..util.cli import run_check
from .globals import Var


FIX_RANKS = ['domain', 'phylum', 'class', 'order', 'family', 'genus']
CONF_COLS = [rank + '_conf' for rank in FIX_RANKS]


def _demangle(name):
    return re.sub(r' \(taxid:\d+\)', '', name)


@lru_cache()
def _get_fixRank():
    #
    with open(Var.out_allRank_flpth) as fh: lines = fh.readlines()

    #
    id_l = []
    for line in lines:
        id_l.append(line.split()[0])
    #
    df_fix = pd.DataFrame(
        index=id_l, 
        columns=[e for tup in zip(FIX_RANKS, CONF_COLS) for e in tup]
    )

    tp = TimePartition()
    
    # enum all records
    for line, (id, row) in zip(lines, df_fix.iterrows()):
        toks = line.strip().split('\t')

        assert id == toks[0]
        info = toks[2:]
        n = len(info) // 3
        names = [info[i*3] for i in range(n)]
        ranks = [info[i*3+1] for i in range(n)]
        confs = [info[i*3+2] for i in range(n)]

        replace_cols = []
        replace_vals = []
        # enum ranks in record
        for name, rank, conf in zip(names, ranks, confs):
            if rank in FIX_RANKS:
                name = _demangle(name)
                replace_cols.extend([rank, rank + '_conf']) 
                replace_vals.extend([name, conf])

        row[replace_cols] = replace_vals

    tp.emit('For loop')
        
    return df_fix


def get_fixRank():
    df_fix = _get_fixRank()
    return df_fix.copy()


def get_filtered_fixRank():
    df_fix = get_fixRank()

    for _, row in df_fix.iterrows():
        for rank, conf_col in zip(FIX_RANKS[::-1], CONF_COLS[::-1]):
            conf = float(row[conf_col])
            if np.isnan(conf): # no rank
                continue
            elif conf < Var.params.getd('conf'): # filtered rank
                row[conf_col] = np.nan
                row[rank] = np.nan
            else: # unfiltered ranks now
                break

    return df_fix


def get_fix_filtered_id2tax():
    df = get_filtered_fixRank()[FIX_RANKS]

    def row_2_tax(row):
        tax = ';'.join(['' if type(e) is float and np.isnan(e) else e for e in list(row)]) # fixed rank taxon names
        tax = tax.strip(';') + ';'
        if tax == ';': tax = ''
        return tax

    id2tax = df.apply(
        lambda row: row_2_tax(row),
        axis=1
    ).to_dict()

    return id2tax


def parse_shortSeq():
    with open(Var.out_shortSeq_flpth) as fh:
        ids = [id.strip() for id in fh.read().strip().splitlines() if len(id.strip()) > 0]

    return ids



