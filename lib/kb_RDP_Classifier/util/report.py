import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys, os
import json
import shutil
import logging
import uuid

pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 15)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 14)


from .config import _globals

DEFAULT_PNG_SHAPE = (500, 700) # plotly's

class Parser:

    def __init__(self, fixRank_flpth, filterByConf_flpth, conf: float):
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



# TODO make colors for taxa match across graphs

####################################################################################################
####################################################################################################
####################################################################################################
def do_pie_chart(parser, png_flpth, html_flpth):

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
            'text': 'Assignment Cutoff (bootstrap threshold=%.2f)' % parser.conf,
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
            }
    )

    fig.write_image(png_flpth, width=int(DEFAULT_PNG_SHAPE[1] * 1.5))
    fig.write_html(html_flpth)



####################################################################################################
####################################################################################################
####################################################################################################
def do_sunburst(parser, png_flpth, html_flpth):
    # TODO cut out unassigned branches? - save text/space

    logging.info('Generating sunburst')

    df = parser.parse_filterByConf()
    print(df)

    fig = px.sunburst(df, path=df.columns.tolist())

    fig.update_layout(
        title_text='Taxonomic Assignment (bootstrap threshold=%.2f)' % parser.conf,
        title_x=0.5,
    )

    fig.write_image(png_flpth, width=900, height=900)
    fig.write_html(html_flpth)#, default_height=1000)




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

    def __init__(self, out_files, params_prose, cmd_l):
        '''
        out_files - [fixRank, filterByConf]
        params_prose - all str
        '''
        self.replacement_d = {}

        self.parser = Parser(out_files[0], out_files[1], float(params_prose['conf']))

        #
        self.params_prose = params_prose
        self.cmd_l = cmd_l

        #
        self.report_dir = os.path.join(_globals.shared_folder, str(uuid.uuid4()))
        os.mkdir(self.report_dir)


    def _compile_cmd(self):
        
        txt = ''

        for cmd in self.cmd_l:
            txt += '<p><code>' + cmd + '</code></p>\n'

        self.replacement_d['CMD_TAG'] = txt


    def _compile_figures(self):
        #
        self.fig_dir = os.path.join(self.report_dir, 'fig')
        os.mkdir(self.fig_dir)


        #
        figname_l = ['histogram', 'pie_chart', 'sunburst']
        png_flpth_l = [os.path.join(self.fig_dir, figname + '.png') for figname in figname_l]
        html_flpth_l = [os.path.join(self.report_dir, figname + '_plotly.html') for figname in figname_l]

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
        html_flpth = os.path.join(self.report_dir, 'report.html')

        with open(REPORT_HTML_TEMPLATE_FLPTH, 'r') as src_fp:
            with open(html_flpth, 'w') as dst_fp:
                for line in src_fp:
                    if line.strip() in self.replacement_d:
                        dst_fp.write(self.replacement_d[line.strip()])
                    else:
                        dst_fp.write(line)
        

        return self.report_dir, html_flpth

