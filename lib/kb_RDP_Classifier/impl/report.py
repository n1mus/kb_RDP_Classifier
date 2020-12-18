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


pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 15)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 14)


#DEFAULT_PNG_SHAPE = (500, 700) # plotly's
REPORT_HEIGHT= 1000 # px, report window in app cell
IFRAME_HEIGHT = REPORT_HEIGHT - 30
MAX_DATA = 300 # threshold for static
DO_STATIC = True #True # toggle the hiding behind static thing

# TODO (nice-to-have) separate plotly js library into dir
# TODO testing graph info

# TODO histogram 50by30 domain fcked
# TODO pie 0s pile up onto title, but rotating makes labels overlap
# TODO pie better hovertemplate
# TODO sunburst make sure phyla colors don't border
# TODO sunburst open interactivity in iframe https://www.w3schools.com/html/tryit.asp?filename=tryhtml_iframe_target




####################################################################################################
####################################################################################################
####################################################################################################
def do_pie_hist(html_flpth):

    palette = px.colors.qualitative.D3

    logging.info('Generating pie charts')

    df, tax_lvls, conf_cols = app_file.parse_fixRank()

    counts = {'root': 0, **{tax_lvl: 0 for tax_lvl in tax_lvls}}


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
        
    dprint('counts',run='py')

    # sanity check
    acc = 0
    for _, count in counts.items():
        acc += count
    assert acc == len(df)

    # remove 0 counts to avoid label stacking into top margin
    counts = {tax_lvl: count for tax_lvl, count in counts.items() if count != 0}

    #
    trace0 = go.Pie(
        labels=list(counts.keys())[::-1], # rev so color matches hist
        values=list(counts.values())[::-1], 
        textinfo='label+percent', 
        hovertemplate=(
            '%{label} <br>'
            '%{percent} <br>'
            '%{value}/' + str(df.shape[0]) + ' amplicons'
            '<extra></extra>'
        ),
        sort=False,
        #rotation=90, # try to get 0s out of title. this num means 'genus' sector will end at 90 and 'family' will begin at 90
        showlegend=False,
        marker_colors=palette
    )
    
    logging.info('Generating histogram') 

    hovertemplate = (
        'Rank: %s <br>'
        'Confidence bin: %%{customdata[0]} <br>' # TODO confidence before proportion
        'Proportion of amplicons: %%{y:.4g} <br>'
        'Amplicon count: %%{customdata[1]}/%d <br>'
        '<extra></extra>'
    )
    bin_s_l = ['[%g, %g)' % (i/10, i/10+.1) for i in range(10)]

    trace1_l = []
    for i, (conf_col, tax_lvl) in enumerate(zip(conf_cols[::-1], tax_lvls[::-1])):
        conf_l = df[conf_col].tolist()
        conf_l = [conf if conf<1 else conf-1e-8 for conf in conf_l] # nudge 1.0 confidences below
        h = np.histogram(conf_l, range=[0,1], bins=10)[0]
        #if tax_lvl != 'domain':
        #    continue
        customdata = list(zip(bin_s_l, h)) 
        #dprint('tax_lvl','conf_l','h','customdata',max_lines=None,run='py')
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
                name=tax_lvl + ' '*100, 
                customdata=customdata,
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
            'Taxonomy Cutoff Rank (conf=%s)' % Var.params.prose_args['conf'],
            'Bootstrap Confidence Histogram, <br> By Rank',
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
            itemclick='toggleothers',
            itemdoubleclick='toggle',
        ),
    )

    fig.write_html(html_flpth)

    return False



####################################################################################################
####################################################################################################
####################################################################################################
def do_sunburst(html_flpth,png_flpth):
    # TODO don't show phylum on hover text/label (but keep using it for color)

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
        title_text='Taxonomic Assignment (conf=%s)' % Var.params.prose_args['conf'],
        title_x=0.5,
    )

    fig.write_html(html_flpth)

    if DO_STATIC and len(names) > MAX_DATA:# whether to hide behind static image

        fig.write_image(png_flpth, width=900, height=IFRAME_HEIGHT)
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
        self.fig_dir = os.path.join(Var.report_dir, 'fig')
        os.mkdir(self.fig_dir)

        #
        pie_hist_html_flpth = os.path.join(Var.report_dir, 'pie_hist.html')
        sunburst_html_flpth = os.path.join(Var.report_dir, 'sunburst.html')
        sunburst_png_flpth = os.path.join(Var.report_dir, 'sunburst.png')


        #
        do_pie_hist(pie_hist_html_flpth)
        hide_b = do_sunburst(sunburst_html_flpth, sunburst_png_flpth)


        #
        def get_relative_fig_path(flpth):
            return '/'.join(flpth.split('/')[-2:])

        #
        link_out_img_s = (
            '<div id="imgLink">\n'
            '<a href="%s" target="_blank">\n'
            '<img alt="%s" src="%s" title="Open to interact">\n'
            '</a>\n' 
            '</div>\n'
        )
        iframe_s = (
            '<iframe src="%s" '
            'scrolling="no" '
            'seamless="seamless" '
            'style="border:none;">'
            '</iframe>\n'
        )

        #
        self.replacements['PIE_HIST_TAG'] = (
            iframe_s % os.path.basename(pie_hist_html_flpth)
        )

        self.replacements['SUNBURST_TAG'] = (
            iframe_s % os.path.basename(sunburst_html_flpth)
            if not hide_b else
            link_out_img_s % (
                os.path.basename(sunburst_html_flpth),
                get_relative_fig_path(sunburst_png_flpth),
                get_relative_fig_path(sunburst_png_flpth),
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
                        dst_fh.write(self.replacements[line.strip()])
                    else:
                        dst_fh.write(line)

        return html_flpth





'''
Fullscreen button
https://www.w3schools.com/howto/howto_js_fullscreen.asp
https://www.w3schools.com/howto/tryit.asp?filename=tryhow_js_fullscreen
https://codepen.io/ssk7833/pen/mVOXXp


Example tabs:
-----------------------


<div class="tab">
<button class="tablinks" onclick="opentab(event, &#39;commands&#39;)">Cmd</button>
<button class="tablinks" onclick="opentab(event, &#39;bootstrap_pie&#39;)">Bootstrap Confidence Pie</button>
<button class="tablinks" onclick="opentab(event, &#39;bootstrap_hist&#39;)">Bootstrap Confidence Histogram</button>
<button class="tablinks active" onclick="opentab(event, &#39;tax_sunburst&#39;)">Taxonomy</button>
</div>


<div id="command" class="tabcontent" style="display: none;">
<p><code>Hello</code></p>
<p><code>Hi</code></p>
</div>

<div id="pie" class="tabcontent" style="display: none;">
<iframe height="100%" width="100%" src="./plotly_pie.html" style="border:none;"></iframe>
</div>

<div id="hist" class="tabcontent" style="display: none;">
<iframe height="100%" width="100%" src="./plotly_hist.html" style="border:none;"></iframe>
</div>

<div id="sunburst" class="tabcontent" style="display: none;">
<iframe height="100%" width="100%" src="./plotly_sunburst.html" style="border:none;"></iframe>
</div>

<div id="sunburst" class="tabcontent" style="display: none;">
<div id="imgLink">
<a href="./plotly_sunburst.html" target="_blank">
<img alt="plotly_sunburst.png" src="./fig/plotly_sunburst.html" title="Open to interact">
</a>
</div>
</div>


'''
