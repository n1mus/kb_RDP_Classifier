import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys, os
import json
import shutil
import logging
import uuid

from .config import Var


pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 15)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 14)


DEFAULT_PNG_SHAPE = (500, 700) # plotly's

# TODO testing graph info

class Parser:

    def __init__(self, fixRank_flpth, filterByConf_flpth):
        self.fixRank_flpth = fixRank_flpth
        self.filterByConf_flpth = filterByConf_flpth


    def parse_filterByConf(self):

        # index is amplicon id
        # rest of cols are domain-genus
        df = pd.read_csv(self.filterByConf_flpth, sep='\t', index_col=0) 
        return df


    def parse_fixRank(self):
        
        # index is amplicon id

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
def do_pie(parser, png_flpth, html_flpth):

    logging.info('Generating pie charts')

    df, tax_lvls, conf_cols = parser.parse_fixRank()

    counts = {'root': 0, **{tax_lvl: 0 for tax_lvl in tax_lvls}}
    print(counts)


    # iterate through df rows
    # count last tax lvl to make cutoff 
    for index, row in df.iterrows():
        confs = {tax_lvl: row[conf_col] for tax_lvl, conf_col in zip(tax_lvls, conf_cols)}
        
        tax_lvl_last = 'root'
        for tax_lvl in tax_lvls:
            if confs[tax_lvl] < Var.params.getd('conf'):
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
        labels=list(counts.keys())[::-1], # rev so color matches hist
        values=list(counts.values())[::-1], 
        textinfo='label+percent', 
        sort=False
    )])
    
    fig.update_layout(
        title={
            'text': 'Assignment Cutoff (bootstrap threshold=%s)' % Var.params.rdp_prose['conf'],
            'x': 0.5,
        },
        showlegend=False
    )

    fig.write_image(png_flpth)
    fig.write_html(html_flpth)


####################################################################################################
####################################################################################################
####################################################################################################
def do_histogram(parser, png_flpth, html_flpth):

    logging.info('Generating histogram') 

    df, tax_lvls, conf_cols = parser.parse_fixRank()
    print(df)

    conf_all = []
    for conf_col in conf_cols:
        conf_all += df[conf_col].to_list()

    MAX_BINS = 11

    fig = go.Figure()
    for conf_col, tax_lvl in zip(conf_cols[::-1], tax_lvls[::-1]):
        fig.add_trace(go.Histogram(x=df[conf_col].tolist(), name=tax_lvl, histnorm='probability', xbins={'start': 0, 'end': 1, 'size': 0.1}))

    fig.add_trace(go.Histogram(x=conf_all, name='pooled', histnorm='probability', nbinsx=MAX_BINS, marker_color='black'))

    fig.update_layout(
        yaxis_title_text='Proportion',
        xaxis_title_text='Bootstrap Confidence',
        title_text='Bootstrap Confidence Histogram',
        title_x=0.5,
        xaxis = {
            'tickmode': 'linear',
            'tick0': 0,
            'dtick': 0.1
        },
        yaxis_range=[0, 1],
    )

    fig.write_image(png_flpth, width=int(DEFAULT_PNG_SHAPE[1] * 1.5))
    fig.write_html(html_flpth)



####################################################################################################
####################################################################################################
####################################################################################################
def do_sunburst(parser, png_flpth, html_flpth):
    # TODO cut out unassigned branches? - save text/space
    # TODO don't show phylum on hover text/label (but keep using it for color)

    logging.info('Generating sunburst')

    df = parser.parse_filterByConf()
    print(df)

    fig = px.sunburst(df, path=df.columns.tolist(), color='phylum')

    fig.update_layout(
        title_text='Taxonomic Assignment (bootstrap threshold=%s)' % Var.params.rdp_prose['conf'],
        title_x=0.5,
    )

    fig.write_image(png_flpth, width=900, height=900)
    fig.write_html(html_flpth)#, default_height=1000) # TODO zoom a little? more color?




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

    def __init__(self, out_files, cmd_l):
        '''
        out_files - [*fixRank*, *filterByConf*]
        '''
        self.replacement_d = {}
        self.parser = Parser(out_files[0], out_files[1])
        self.cmd_l = cmd_l



    def _compile_cmd(self):
        
        txt = ''

        for cmd in self.cmd_l:
            txt += '<p><code>' + cmd + '</code></p>\n'

        self.replacement_d['CMD_TAG'] = txt


    def _compile_figures(self):
        #
        self.fig_dir = os.path.join(Var.report_dir, 'fig')
        os.mkdir(self.fig_dir)

        #
        figname_l = ['histogram', 'pie', 'sunburst']
        png_flpth_l = [os.path.join(self.fig_dir, figname + '.png') for figname in figname_l]
        html_flpth_l = [os.path.join(Var.report_dir, figname + '_plotly.html') for figname in figname_l]
        figfunc_l = ['do_' + figname for figname in figname_l]

        # call plotly-doing functions
        for png_flpth, html_flpth, figfunc in zip(png_flpth_l, html_flpth_l, figfunc_l):
            globals()[figfunc](self.parser, png_flpth, html_flpth)

        def get_relative_fig_path(flpth):
            return '/'.join(flpth.split('/')[-2:])

        # build replacement string
        txt = '<div id="imgLink">\n'
        for png_flpth, html_flpth in zip(png_flpth_l, html_flpth_l):
            txt += '<p><a href="%s" target="_blank"><img alt="%s" src="%s" title="Open to interact"></a></p>\n' % (
                os.path.basename(html_flpth),
                os.path.basename(png_flpth),
                get_relative_fig_path(png_flpth))

        txt += '</div>\n'

        self.replacement_d['FIGURES_TAG'] = txt


    def write(self):
        self._compile_cmd()
        self._compile_figures()

        
        REPORT_HTML_TEMPLATE_FLPTH = '/kb/module/ui/output/report.html'
        html_flpth = os.path.join(Var.report_dir, 'report.html')

        with open(REPORT_HTML_TEMPLATE_FLPTH) as src_fh:
            with open(html_flpth, 'w') as dst_fh:
                for line in src_fh:
                    if line.strip() in self.replacement_d:
                        dst_fh.write(self.replacement_d[line.strip()])
                    else:
                        dst_fh.write(line)

        return html_flpth

