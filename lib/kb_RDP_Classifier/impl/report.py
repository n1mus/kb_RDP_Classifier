import plotly.express as px
import plotly.graph_objects as go
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
REPORT_HEIGHT= 800 # px
IFRAME_HEIGHT = REPORT_HEIGHT - 30
MAX_DATA = 300 # threshold for static
DO_STATIC = False #True # toggle the hiding behind static thing

# TODO (nice-to-have) separate plotly js library into dir
# TODO testing graph info

# TODO histogram 50by30 domain fcked
# TODO pie 0s pile up onto title, but rotating makes labels overlap
# TODO pie better hovertemplate
# TODO sunburst make sure phyla colors don't border




####################################################################################################
####################################################################################################
####################################################################################################
def do_pie(png_flpth, html_flpth):

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
    fig = go.Figure(data=[go.Pie(
        labels=list(counts.keys())[::-1], # rev so color matches hist
        values=list(counts.values())[::-1], 
        textinfo='label+percent', 
        sort=False,
        #rotation=90, # try to get 0s out of title. this num means 'genus' sector will end at 90 and 'family' will begin at 90
    )])
    
    fig.update_layout(
        title=dict(
            text='Cutoff Rank (conf=%s)' % Var.params.prose_args['conf'],
            x=0.5,
        ),
        showlegend=False
    )

    #fig.write_image(png_flpth)
    fig.write_html(html_flpth)

    return False


####################################################################################################
####################################################################################################
####################################################################################################
def do_histogram(png_flpth, html_flpth):

    logging.info('Generating histogram') 

    df, tax_lvls, conf_cols = app_file.parse_fixRank()

    hovertemplate = (
        'Rank: %s <br>'
        'Proportion of %s taxa: %%{y:.4g} <br>'
        'Confidence bin: %%{customdata[0]} <br>' # TODO confidence before proportion
        'Amplicon count: %%{customdata[1]}/%d <br>'
        '<extra></extra>'
    )
    bin_s_l = ['[%g, %g)' % (i/10, i/10+.1) for i in range(10)]

    '''
    def filtered_customdata(h, bin_s_l):
        h_filtered = [ct for ct in h if ct>0]
        bin_s_l_filtered = [bin_s for ct, bin_s in zip(h, bin_s_l) if ct>0]
        assert len(bin_s_l_filtered) == len(np.nonzero(h)[0])
        assert len(h_filtered) == len(np.nonzero(h)[0])
        return list(zip(bin_s_l_filtered, h_filtered, ))
    '''

    fig = go.Figure()
    for conf_col, tax_lvl in zip(conf_cols[::-1], tax_lvls[::-1]):
        conf_l = df[conf_col].tolist()
        conf_l = [conf if conf<1 else conf-1e-8 for conf in conf_l] # nudge 1.0 confidences below
        h = np.histogram(conf_l, range=[0,1], bins=10)[0]
        #if tax_lvl != 'domain':
        #    continue
        customdata = list(zip(bin_s_l, h)) 
        '''(
            filtered_customdata(h, bin_s_l)
            if h[0] == 0 or h[-1] == 0 # starting with 0s seems to break binning start,
            else list(zip(bin_s_l, h))
        )'''
        #dprint('tax_lvl','conf_l','h','customdata',max_lines=None,run='py')
        fig.add_trace(
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
                    tax_lvl,
                    len(conf_l),
                ),
            ))

    '''
    conf_all = []
    for conf_col in conf_cols:
        conf_all += df[conf_col].to_list()
    h = np.histogram(conf_all, range=[0,1], bins=10)[0]
    fig.add_trace(
        go.Histogram(
            x=conf_all, 
            name='pooled', 
            histnorm='probability', 
            xbins={'start': 0, 'end': 1, 'size': 0.1},
            marker_color='black',
            customdata=list(zip(bin_s_l, h)),
            hovertemplate=hovertemplate % (
                'Pooled',
                'pooled',
                len(conf_all)
            )
        ))
    '''

    fig.update_layout(
        title=dict(
            text='Bootstrap Confidence Histogram, <br> By Rank',
            x=0.5,
        ),
        xaxis=dict( 
            tickmode='linear',
            tick0=0,
            dtick=0.1,
            range=[0,1],
            title_text='Bootstrap Confidence',
        ),
        yaxis=dict(
            tick0=0,
            dtick=0.1,
            range=[0,1],
            title_text='Proportion of Taxa',
        ),
        legend=dict( # move legend to left since ifrom cuts off text when right 
            x=-0.1,
            xanchor='right',
            traceorder='grouped',
            itemclick='toggleothers',
            itemdoubleclick='toggle',
            #title_text='TITLE0123456789',
            #title_side='left',
        ),
    )

    #fig.write_image(png_flpth, width=int(DEFAULT_PNG_SHAPE[1] * 1.5))
    fig.write_html(html_flpth)

    return False



####################################################################################################
####################################################################################################
####################################################################################################
def do_sunburst(png_flpth, html_flpth):
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

    tab_div_s = (
        '<div id="%s" class="tabcontent" style="display: %s;">\n'
        '%s'
        '</div>\n'
    )

    def __init__(self, cmd_l):
        '''
        '''
        self.cmd_l = cmd_l
        self.tabdiv_l = []



    def _compile_cmd_tab(self):
        
        txt = ''

        for cmd in self.cmd_l:
            txt += '<p><code>' + cmd + '</code></p>\n'

        txt = self.tab_div_s % (
            'commands',
            'none',
            txt,
        )

        self.tabdiv_l.append(txt)


    def _compile_figure_tabs(self):
        #
        self.fig_dir = os.path.join(Var.report_dir, 'fig')
        os.mkdir(self.fig_dir)

        #
        figname_l = ['sunburst', 'histogram', 'pie']
        png_flpth_l = [os.path.join(self.fig_dir, figname + '.png') for figname in figname_l]
        html_flpth_l = [os.path.join(Var.report_dir, figname + '.html') for figname in figname_l]
        figfunc_l = ['do_' + figname for figname in figname_l]
        hide_l = []

        # call plotly-doing functions
        for png_flpth, html_flpth, figfunc in zip(png_flpth_l, html_flpth_l, figfunc_l):
            hide_b = globals()[figfunc](png_flpth, html_flpth)
            hide_l.append(hide_b)

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
            '<iframe src="%s" title="plotly" '
            'scrolling="no" seamless="seamless" '
            f'height="{IFRAME_HEIGHT}px" width="100%%" '
            'style="border:none;">'
            '</iframe>\n'
        )


        # make a div for each fig
        for figname, png_flpth, html_flpth, hide_b in zip(figname_l, png_flpth_l, html_flpth_l, hide_l):
            if hide_b:
                intxt = link_out_img_s % (
                    os.path.basename(html_flpth),
                    os.path.basename(png_flpth),
                    get_relative_fig_path(png_flpth),
                )
            else:
                intxt = iframe_s % os.path.basename(html_flpth)

            divtxt = self.tab_div_s % (
                figname,
                ('block' if figname == 'sunburst' else 'none'),
                intxt,
            )

            self.tabdiv_l.append(divtxt)



    def write(self):
        self._compile_cmd_tab()
        self._compile_figure_tabs()

        
        html_flpth = os.path.join(Var.report_dir, 'report.html')

        with open(Var.report_template_flpth) as src_fh:
            with open(html_flpth, 'w') as dst_fh:
                for line in src_fh:
                    if line.strip() == 'REPLACE_TAG':
                        for divtxt in self.tabdiv_l:
                            dst_fh.write(divtxt + '\n')
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
