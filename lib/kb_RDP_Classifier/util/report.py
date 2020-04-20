#!/home/sumin/anaconda3/bin/python

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys, os
import json
import shutil
import logging

pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 15)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 14)


from .config import _globals



class Parser:

    def __init__(self, fixRank_flpth, filterByConf_flpth, conf):
        self.fixRank_flpth = fixRank_flpth
        self.filterByConf_flpth = filterByConf_flpth
        self.conf = conf


    def parse_filterByConf(self):
        
        df = pd.read_csv(self.filterByConf_flpth, sep='\t', index_col=0)
        return df


    def parse_fixRank(self):
        
        df = pd.read_csv(self.fixRank_flpth, sep='\t', header=None, 
            names=['sequence', 'domain', 'domain_conf', 'phylum', 'phylum_conf', 'class', 'class_conf', 
            'order', 'order_conf', 'family', 'family_conf', 'genus', 'genus_conf'], 
            index_col=0, usecols=[0, 2, 4, 5, 7, 8, 10, 11, 13, 14, 16, 17, 19])

        tax_lvls = ['domain', 'phylum', 'class', 'order', 'family', 'genus']
        conf_cols = [tax_lvl + '_conf' for tax_lvl in tax_lvls]

        return df, tax_lvls, conf_cols





####################################################################################################
####################################################################################################
####################################################################################################
def do_pie_chart(parser):

    logging.info('Generating pie chart')

    df, tax_lvls, conf_cols = parser.parse_fixRank()

    counts = {'root': 0, **{tax_lvl: 0 for tax_lvl in tax_lvls}}
    print(counts)


    # iterate through df rows
    # count last tax lvl to make cutoff 
    for index, row in df.iterrows():
        confs = {tax_lvl: row[conf_col] for tax_lvl, conf_col in zip(tax_lvls, conf_cols)}
        
        tax_lvl_last = 'root'
        for tax_lvl in tax_lvls:
            if confs[tax_lvl] < parser.conf:
                counts[tax_lvl_last] += 1
                break
            else:
                tax_lvl_last = tax_lvl
        if tax_lvl_last == tax_lvls[-1]:
            counts[tax_lvl_last] += 1
        
    print(json.dumps(counts, indent=3))

    # sanity check
    acc = 0
    for _, count in counts.items():
        acc += count
    assert acc == len(df)


    #
    fig = go.Figure(data=[go.Pie(
        labels=list(counts.keys()), values=list(counts.values()), textinfo='label+percent', sort=False)])
    
    fig.update_layout(
        title={
            'text': 'Assignment Cutoff',
            'x': 0.25,
        },
        showlegend=False
    )

    return fig.to_html(full_html=False)


####################################################################################################
####################################################################################################
####################################################################################################
def do_histogram(parser):

    logging.info('Generating histogram')

    df, tax_lvls, conf_cols = parser.parse_fixRank()
    print(df)

    '''
    num_lvls = len(tax_lvls)

    num_colors = num_lvls
    inc = int(256 / (num_colors - 1))
    RGB_up = [i * inc for i in range(num_colors)]
    RGB_down = RGB_up[::-1]

    blue_yellow = ['rgb(' + str(RGB_up[i]) + ',' + str(RGB_up[i]) + ',' + str(RGB_down[i]) + ')' for i in range(num_colors)]

    print(blue_yellow)
    '''

    conf_all = []
    for conf_col in conf_cols:
        conf_all += df[conf_col].to_list()

    MAX_BINS = 11

    fig = go.Figure()
    for conf_col, tax_lvl in zip(conf_cols[::-1], tax_lvls[::-1]):
        fig.add_trace(go.Histogram(x=df[conf_col].tolist(), name=tax_lvl, histnorm='probability', nbinsx=MAX_BINS))

    fig.add_trace(go.Histogram(x=conf_all, name='all', histnorm='probability', nbinsx=MAX_BINS, marker_color='black'))

    fig.update_layout(
        yaxis_title_text='Proportion of Assigned Sequences',
        xaxis_title_text='Bootstrap Confidence',
        title_text='Bootstrap Confidence Histogram',
        title_x=0.25
    )

    return fig.to_html(full_html=False)



####################################################################################################
####################################################################################################
####################################################################################################
def do_sunburst(parser):
    # TODO include unassigned domain
    # TODO cut out unassigned branches? - save text/space

    logging.info('Generating sunburst')

    df = parser.parse_filterByConf()
    print(df)

    fig = px.sunburst(df, path=df.columns.tolist())

    fig.update_layout(
        title_text='Taxonomic Assignment',
        title_x=0.25
    )

    return fig.to_html(full_html=False)



##########
####################
##############################
########################################
##################################################
############################################################
######################################################################
################################################################################
##########################################################################################
####################################################################################################
####################################################################################################
####################################################################################################

class HTMLReportWriter:

    def __init__(self, fixRank_flpth, filterByConf_flpth, conf):
        self.replacement_d = {}

        self.parser = Parser(fixRank_flpth, filterByConf_flpth, conf)

    def compile_figures(self):
        txt = ''

        txt += do_sunburst(self.parser)
        txt += do_histogram(self.parser)
        txt += do_pie_chart(self.parser)

        self.replacement_d['FIGURES_TAG'] = txt

    def write(self):
        self.compile_figures()

        REPORT_HTML_TEMPLATE_FLPTH = '/kb/module/ui/output/report.html'
        html_flpth = os.path.join(_globals.run_dir, 'report.html')

        with open(REPORT_HTML_TEMPLATE_FLPTH, 'r') as src_fp:
            with open(html_flpth, 'w') as dst_fp:
                for line in src_fp:
                    if line.strip() in self.replacement_d:
                        dst_fp.write(self.replacement_d[line.strip()])
                    else:
                        dst_fp.write(line)
        
        self.html_flpth = html_flpth


