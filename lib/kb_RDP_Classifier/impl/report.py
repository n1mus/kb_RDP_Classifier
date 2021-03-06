import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import sys, os
import json
import shutil
import logging
import uuid

from ..util.debug import dprint
from .globals import Var
from .ds import TaxTree
from . import app_file

'''
pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 15)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 14)
'''

REPORT_HEIGHT= 800 # px, report window in app cell. don't make too high for smaller devices
IMG_HEIGHT = REPORT_HEIGHT # px. don't make too big or title will shrink relatively
MAX_DATA = 4000 # threshold for static hiding
DO_STATIC = True # toggle the hiding behind static thing

# TODO **** testing graph info
# TODO (nice-to-have) separate plotly js library into dir

# TODO * sunburst make sure phyla colors don't border
# TODO sunburst needs better loading like pie/hist? loads with text messed up
# TODO sunburst img-link height grows a lot
# TODO histogram user testing data messes it up - get test data
# TODO pie labels run into title ...


####################################################################################################
####################################################################################################
####################################################################################################
def do_pie_hist(html_flpth):

    palette = px.colors.qualitative.D3
    df, tax_lvls, conf_cols = app_file.parse_fixRank()

    logging.info('Generating pie charts')

    # iterate through df rows
    # count last tax lvl to make cutoff 
    counts = {'root': 0, **{tax_lvl: 0 for tax_lvl in tax_lvls}}
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
        
    # sanity check
    acc = 0
    for _, count in counts.items():
        acc += count
    assert acc == len(df)

    # remove 0 counts to avoid label stacking into top margin
    #counts = {tax_lvl: count for tax_lvl, count in counts.items() if count != 0}

    #
    trace0 = go.Pie(
        labels=list(counts.keys())[::-1], # rev so color matches hist
        values=list(counts.values())[::-1], 
        textinfo='label+percent', 
        hovertemplate=(
            'Rank: %{customdata[0]} <br>'
            'Percentage of amplicons: %{percent} <br>'
            'Amplicon count: %{value}/' + str(df.shape[0]) +
            '<extra></extra>'
        ),
        sort=False,
        rotation=90, # try to get 0s out of title. this num means 'genus' sector will end at 90 and 'family' will begin at 90
        showlegend=False,
        marker_colors=palette,
        customdata=[tax_lvl.title() for tax_lvl in list(counts.keys())[::-1]],
    )
    
    logging.info('Generating histogram') 

    hovertemplate = (
        'Rank: %s <br>'
        'Confidence bin: %%{customdata[0]} <br>' # TODO confidence before proportion
        'Proportion of amplicons: %%{y:.3g} <br>'
        'Amplicon count: %%{customdata[1]}/%d <br>'
        '<extra></extra>'
    )
    bin_s_l = [
        ('[%g, %g]' if i==9 else '[%g, %g)') % (i/10, i/10+.1) # plotly hist bin edges are [start,end)
        for i in range(10)
    ]

    def hist(l):
        '''Use np to hist but with [s,e) instead of (s,e] by nudging edges ever so slightly back
        Max values nudged even more back so last bin catches them'''
        d = 1e-15 # femto nudge bin edges back
        h = np.histogram(l, range=[0-d,1-d], bins=10)[0]
        return h

    def clip_customdata(h, *ll):
        '''If h begins with 0s, clip those for customdata'''
        ll = [list(l).copy() for l in ll]
        for v in h:
            if v == 0:
                for l in ll:
                    l.pop(0)
            else:
                break
        return list(zip(*ll))

    trace1_l = []
    for i, (conf_col, tax_lvl) in enumerate(zip(conf_cols[::-1], tax_lvls[::-1])):
        conf_l = df[conf_col].tolist()
        conf_l = [conf if conf<1 else conf-1e-6 for conf in conf_l] # milli nudge 1.0 confidences below
        h = hist(conf_l)
        #customdata = list(zip(bin_s_l, h)) 
        #dprint('tax_lvl','conf_l','h','clip_customdata(h, bin_s_l, h)',max_lines=None,run='py')
        trace1_l.append(
            go.Histogram(
                x=conf_l, 
                xbins=dict(
                    start=0, 
                    end=1,
                    size=0.1,
                ),
                autobinx=False,
                histnorm='probability', 
                name=tax_lvl, 
                customdata=clip_customdata(h, bin_s_l, h),
                hovertemplate=hovertemplate % (
                    tax_lvl.title(),
                    #tax_lvl,
                    len(conf_l),
                ),
                marker_color=palette[i],
            ))

    # subplots

    fig = make_subplots(
        rows=2, 
        cols=1,
        subplot_titles=(
            'Taxonomy Cutoff Rank (conf=%s) <br>' % Var.params.get_prose_args()['conf'],
            'Bootstrap Confidence <br>',
        ),
        specs=[
            [dict(type='pie')],
            [dict(type='xy')],
        ],
        vertical_spacing=0.1,
    )

    fig.add_trace(trace0, row=1, col=1)
    for trace1 in trace1_l:
        fig.add_trace(trace1, row=2, col=1)

    fig.update_xaxes(
        row=2,
        col=1,
        tickmode='linear',
        tick0=0,
        dtick=0.1,
        range=[0,1],
        title_text='Bootstrap Confidence',
    )

    fig.update_yaxes(
        row=2,
        col=1,
        tick0=0,
        dtick=0.2,
        range=[0,1],
        title_text='Proportion of Amplicons',
    )

    fig.update_layout(
        legend=dict(
            y=0.5,
            yanchor='top',
            itemclick='toggleothers',
            itemdoubleclick='toggle',
        ),
        margin_t=40, # px, default 100
    )

    fig.write_html(html_flpth, full_html=False)



####################################################################################################
####################################################################################################
####################################################################################################
def do_sunburst(html_flpth,png_flpth):

    logging.info('Generating sunburst')

    TaxTree.build()
    names, parents, counts, paths, color_ids = TaxTree.get_sunburst_lists() # first el is Root

    palette = px.colors.qualitative.Alphabet
    id2ind = {
        color_id: i 
        for i, color_id 
        in enumerate(
            sorted(list(set(color_ids))) # deterministic unique color_ids
        )
    } # map color ids to int
    colors = ['#FFFFFF'] + [palette[id2ind[color_id] % len(palette)] for color_id in color_ids[1:]] # Root is white

    fig = go.Figure(go.Sunburst(
        ids=paths,
        labels=names,
        parents=parents,
        values=counts,
        marker=dict(
            colors=colors
        ),
        hovertemplate=(
            'Taxon: %{label}<br>'
            'Path: %{id}<br>' # should be rootless TODO
            'Amplicon count: %{value}'
            '<extra></extra>' # hide secondary hover box
        ),
        branchvalues='total',
    ))

    fig.update_layout(
        title_text='Taxonomy (conf=%s)' % Var.params.get_prose_args()['conf'],
        title_x=0.5,
    )

    fig.write_html(html_flpth)

    if DO_STATIC and len(names)*4 > MAX_DATA:# whether to hide behind static image
                                             # 4 because name+path+count+color
        fig.write_image(png_flpth, width=IMG_HEIGHT, height=IMG_HEIGHT)
        return True

    else:
        return False


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

    def __init__(self, cmd_l):
        '''
        '''
        self.cmd_l = cmd_l
        self.tabdiv_l = []

        self.replacements = {}


    def _compile_cmd_tab_body(self):
        
        txt = ''

        for cmd in self.cmd_l:
            txt += '<p><code>' + cmd + '</code></p>\n'

        self.replacements['CMD_TAG'] = txt


    def _compile_figure_tab_bodies(self):

        #
        pie_hist_html_flpth = os.path.join(Var.report_dir, 'pie_hist.html')
        sunburst_html_flpth = os.path.join(Var.report_dir, 'sunburst.html')
        sunburst_png_flpth = os.path.join(Var.report_dir, 'sunburst.png')


        #
        do_pie_hist(pie_hist_html_flpth)
        hide_b = do_sunburst(sunburst_html_flpth, sunburst_png_flpth)


        #
        link_out_img_s = (
            #'<div id="imgLink">\n'
            '<a href="%s" target="_blank" title="Open to interact">\n'
            '<img alt="%s" src="%s">\n'
            '</a>\n' 
            #'</div>\n'
        )
        iframe_s = (
            '<iframe src="%s" '
            'id="%s" '
            'scrolling="no" '
            'seamless="seamless" '
            '></iframe>\n'
        )

        #
        self.replacements['PIE_HIST_TAG'] = (
            iframe_s % (
                os.path.basename(pie_hist_html_flpth),
                'iframe_pie_hist'
            )
        )

        self.replacements['SUNBURST_TAG'] = (
            iframe_s % (
                os.path.basename(sunburst_html_flpth),
                'iframe_sunburst'
            )
            if not hide_b else
            link_out_img_s % (
                os.path.basename(sunburst_html_flpth),
                os.path.basename(sunburst_png_flpth),
                os.path.basename(sunburst_png_flpth),
            )
        )


    def write(self):
        self._compile_cmd_tab_body()
        self._compile_figure_tab_bodies()
        
        html_flpth = os.path.join(Var.report_dir, 'report.html')

        with open(Var.report_template_flpth) as src_fh:
            with open(html_flpth, 'w') as dst_fh:
                for line in src_fh:
                    if line.strip() in self.replacements:
                        dst_fh.write(self.replacements[line.strip()].strip() + '\n')
                    else:
                        dst_fh.write(line)

        return html_flpth





