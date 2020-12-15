'''
For parsing or otherwise manipulating app input and output files
'''
import numpy as np
import pandas as pd
import os

from ..util.cli import run_check
from .globals import Var

def prep_refdata():
    '''
    Refdata is over 100MB Github limit
    Concatenate the split binary here
    '''
    refdata_dir = '/kb/module/data'
    refdata_name = 'SILVA_138_SSU_NR_99'

    cmd = (
        'cd %s && cat %s_* > rejoined && tar xzf rejoined'
        % (refdata_dir, refdata_name)
    )

    run_check(cmd)

    if not os.path.exists(Var.propfile['silva_138_ssu']):
        raise Exception(cmd)


def parse_fixRank():
    
    # index is amplicon id

    df = pd.read_csv(Var.out_fixRank_flpth, sep='\t', header=None, 
        names=['id', 'domain', 'domain_conf', 'phylum', 'phylum_conf', 'class', 'class_conf', 
        'order', 'order_conf', 'family', 'family_conf', 'genus', 'genus_conf'], 
        index_col='id', usecols=[0, 2, 4, 5, 7, 8, 10, 11, 13, 14, 16, 17, 19])

    tax_lvls = ['domain', 'phylum', 'class', 'order', 'family', 'genus']
    conf_cols = [tax_lvl + '_conf' for tax_lvl in tax_lvls]

    return df, tax_lvls, conf_cols


def parse_truncated_fixRank():
    '''
    Create df for plotly sunburst
    
    Get df from fixRank
    Res df should be similar to filterByConf df, but anything below the confidence is `None`
    '''

    df, tax_cols, conf_cols = parse_fixRank()
    df_tax = df[tax_cols]
    df_conf = df[conf_cols]

    for i in range(df.shape[0]):
        a = df_conf.iloc[i,:].values
        cut = np.where(a < Var.params.getd('conf'))[0]
        df_tax.iloc[i,cut] = None

    return df_tax


'''

    def parse_filterByConf(self):

        # index is amplicon id
        # rest of cols are domain-genus
        df = pd.read_csv(self.filterByConf_flpth, sep='\t', index_col=0) 
        return df
'''


def parse_filterByConf(pad_ranks=True) -> dict: # TODO why padding? to get 7 slots?

    NUM_RANKS = 7
    
    # index is amplicon id
    df = pd.read_csv(Var.out_filterByConf_flpth, sep='\t', index_col=0)

    id2taxStr = df.apply(
        lambda row: ';'.join(
            list(row.array) + ([''] * (NUM_RANKS - len(row.array)) if pad_ranks is True else []) 
        ), 
        axis=1
    ).to_dict()

    return id2taxStr


def parse_shortSeq():

    with open(Var.out_shortSeq_flpth) as fh:
        ids = [id.strip() for id in fh.read().strip().splitlines() if len(id.strip()) > 0]

    return ids
