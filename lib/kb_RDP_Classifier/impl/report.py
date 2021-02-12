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
from . import ana
from . import app_file

'''
pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 15)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 14)
'''

IMG_HEIGHT = Var.report_height # px. don't make too big or title will shrink relatively
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

    logging.info('Generating pie charts')
    counts = ana.get_cutoff_rank_counts()
    total = sum([c for c in counts.values()])

    #
    trace0 = go.Pie(
        labels=list(counts.keys())[::-1], # rev so color matches hist
        values=list(counts.values())[::-1], 
        textinfo='label+percent', 
        hovertemplate=(
            'Rank: %{customdata[0]} <br>'
            'Percentage of amplicons: %{percent} <br>'
            'Amplicon count: %{value}/' + str(total) +
            '<extra></extra>'
        ),
        sort=False,
        rotation=90, # try to get 0s out of title. this num means 'genus' sector will end at 90 and 'family' will begin at 90
        showlegend=False,
        marker_colors=palette,
        customdata=[tax_lvl.title() for tax_lvl in list(counts.keys())[::-1]],
    )
    
    logging.info('Generating histogram') 
    rank2confs = ana.get_rank2confs()
    #dprint('rank2confs', max_lines=None)

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
    for i, (rank, conf_l) in list(enumerate(rank2confs.items()))[::-1]:
        h = ana.hist_0_1_10(conf_l)
        #if rank == 'domain': dprint('rank', 'conf_l', 'h', 'len(h)')
        trace1_l.append(
            go.Histogram(
                x=[c if c<1 else c-1e-6 for c in conf_l], # micro nudge right-most max back
                xbins=dict(
                    start=0, 
                    end=1,
                    size=0.1,
                ),
                autobinx=False,
                histnorm='probability', 
                name=rank, 
                customdata=clip_customdata(h, bin_s_l, h),
                hovertemplate=hovertemplate % (
                    rank.title(),
                    len(conf_l),
                ),
                marker_color=palette[i],
            ))

    # subplots

    fig = make_subplots(
        rows=2, 
        cols=1,
        subplot_titles=(
            'Taxonomy Cutoff Rank<br>(conf=%s)' % Var.params.get_prose_args()['conf'],
            'Bootstrap Confidence',
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

    fig.write_html(
        html_flpth, 
        full_html=False
    )



####################################################################################################
####################################################################################################
####################################################################################################
def do_sunburst(html_flpth,png_flpth):

    logging.info('Generating sunburst')

    ana.TaxTree.build()
    names, parents, counts, paths, color_ids = ana.TaxTree.get_sunburst_lists() # first el is Root

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
            'Path: %{id}<br>'
            'Amplicon count: %{value}'
            '<extra></extra>' # hide secondary hover box
        ),
        branchvalues='total',
        sort=False,
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





