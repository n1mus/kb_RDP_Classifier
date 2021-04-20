# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os
import sys
import uuid
import subprocess
import functools
import json
import pandas as pd
import csv
import time
import shutil

from installed_clients.WorkspaceClient import Workspace
from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.KBaseReportClient import KBaseReport
from installed_clients.GenericsAPIClient import GenericsAPI

from .impl.params import Params
from .impl import report
from .impl.globals import Var
from .impl.kbase_obj import  AmpliconMatrix, AttributeMapping
from .impl import app_file 
from .util.debug import dprint
from .util.misc import get_numbered_duplicate
from .util.cli import run_check




#END_HEADER


class kb_RDP_Classifier:
    '''
    Module Name:
    kb_RDP_Classifier

    Module Description:
    A KBase module: kb_RDP_Classifier
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = "https://github.com/kbaseapps/kb_rdp_classifier"
    GIT_COMMIT_HASH = "c4b663e59f21843028649b3af948249da378808b"

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)

        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.workspace_url = config['workspace-url']
        self.shared_folder = config['scratch']
        #END_CONSTRUCTOR
        pass


    def run_classify(self, ctx, params):
        """
        This example function accepts any number of parameters and returns results in a KBaseReport
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_classify

        logging.info(params)

        params = Params(params)
        Var.params = params
        
        '''
        tmp/                                        `shared_folder`
        └── kb_rdp_clsf_<uuid>/                      `run_dir`
            ├── return/                             `return_dir`
            |   ├── cmd.txt
            |   ├── study_seqs.fna
            |   └── RDP_Classifier_output/          `out_dir`
            |       ├── out_allRank.tsv
            |       └── out_fixedRank.tsv
            └── report/                             `report_dir`
                ├── pie_hist.html
                ├── suburst.html
                └── report.html
        '''

        ##
        ## set up globals ds `Var` for this API-method run
        ## which involves making this API-method run's directory structure

        Var.update({
            'run_dir': os.path.join(self.shared_folder, 'kb_rdp_clsf_' + str(uuid.uuid4())),
            'dfu': DataFileUtil(self.callback_url),
            'ws': Workspace(self.workspace_url),
            'gapi': GenericsAPI(self.callback_url, service_ver='dev'),
            'kbr': KBaseReport(self.callback_url),
            'warnings': [],
        })

        os.mkdir(Var.run_dir)

        Var.update({
            'return_dir': os.path.join(Var.run_dir, 'return'),
            'report_dir': os.path.join(Var.run_dir, 'report'),
        })

        os.mkdir(Var.return_dir)
        os.mkdir(Var.report_dir)

        Var.update({
            'out_dir': os.path.join(Var.return_dir, 'RDP_Classifier_output')
        })

        os.mkdir(Var.out_dir)




        # cat and gunzip SILVA refdata
        # which has been split into ~99MB chunks to get onto Github
        #if params.is_custom():
        #    app_file.prep_refdata()


        #
        ##
        ### load objects
        ####
        #####

        amp_mat = AmpliconMatrix(params['amp_mat_upa'])
        row_attr_map_upa = amp_mat.obj.get('row_attributemapping_ref')

        create_row_attr_map = row_attr_map_upa is None
        row_attr_map = AttributeMapping(row_attr_map_upa, amp_mat=amp_mat)  


        #
        ##
        ### cmd
        ####
        #####

        fasta_flpth = os.path.join(Var.return_dir, 'study_seqs.fna')
        Var.out_allRank_flpth = os.path.join(Var.out_dir, 'out_allRank.tsv')
        Var.out_shortSeq_flpth = os.path.join(Var.out_dir, 'out_unclassifiedShortSeqs.txt') # seqs too short to classify

        shutil.copyfile(amp_mat.get_fasta(), fasta_flpth)

        cmd = (  
            'java -Xmx4g -jar %s classify %s ' % (Var.classifier_jar_flpth, fasta_flpth) 
            + ' '.join(params.cli_args) + ' '
            + '--format allRank '
            + '--outputFile %s --shortseq_outfile %s' % (Var.out_allRank_flpth, Var.out_shortSeq_flpth)
        )

        run_check(cmd)



        #
        ##
        ### extract classifications
        ####
        #####

        id2taxStr = app_file.get_fix_filtered_id2tax() 

        # get ids of classified and unclassified seqs
        shortSeq_id_l = app_file.parse_shortSeq() # sequences too short to get clsf
        classified_id_l = list(id2taxStr.keys())

        # make sure classifieds and shorts complement
        if Var.debug:
            ret = sorted(classified_id_l + shortSeq_id_l)
            mat = sorted(amp_mat.obj['data']['row_ids'])
            assert ret == mat, \
                'diff1: %s, diff2: %s' % (set(ret)-set(mat), set(mat)-set(ret))

        if len(classified_id_l) == 0: 
            raise Exception('No sequences were long enough to be classified')

        # add in id->'' for unclassified seqs
        # so id2taxStr_l is complete
        # so no KeyErrors later
        for shortSeq_id in shortSeq_id_l:
            id2taxStr[shortSeq_id] = ''

        # add to globals for testing
        Var.shortSeq_id_l = shortSeq_id_l


        #
        ##
        ### add to row AttributeMapping
        ####
        #####

        prose_args = params.get_prose_args()

        attribute = (
            'RDP Classifier Taxonomy (conf=%s, gene=%s)' 
            % (prose_args['conf'], prose_args['gene'])
        )
        attribute_names = row_attr_map.get_attribute_names()
        if attribute in attribute_names:
            attribute = get_numbered_duplicate(attribute_names, attribute)

        source = 'RDP Classifier'

        ind, attribute = row_attr_map.add_attribute_slot(attribute, source)
        row_attr_map.update_attribute(ind, id2taxStr)


        #
        ##
        ### save obj
        ####
        #####

        amp_mat_output_name = Var.params['output_name']
        attr_map_output_name = (
            amp_mat_output_name + '.Amplicon_attributes' if create_row_attr_map else
            None
        )

        row_attr_map_upa_new = row_attr_map.save(name=attr_map_output_name)

        amp_mat.obj['row_attributemapping_ref'] = row_attr_map_upa_new
        amp_mat_upa_new = amp_mat.save(amp_mat_output_name)

        objects_created = [
            dict( # row AttrMap
                ref=row_attr_map_upa_new, 
                description='%sAdded attribute `%s`' % (
                    'Created. ' if create_row_attr_map else '',
                    attribute,
                )
            ),
            dict( # AmpMat
                ref=amp_mat_upa_new, 
                description='Updated amplicon AttributeMapping reference to `%s`' % row_attr_map_upa_new
            ),
        ]


        # testing
        if Var.debug:
            Var.update(dict(
                amp_mat=amp_mat,
                row_attr_map=row_attr_map,
            ))




        #
        ##
        ### html report
        ####
        #####

        hrw = report.HTMLReportWriter(
            cmd_l=[cmd]
        )


        html_flpth = hrw.write()


        html_links = [{
            'path': Var.report_dir,
            'name': os.path.basename(html_flpth),
        }]



        #
        ##
        ###
        ####
        #####

        file_links = [{
            'path': Var.run_dir,
            'name': 'RDP_Classifier_results.zip',
            'description': 'Input, output'
        }]

        params_report = {
            'warnings': Var.warnings,
            'objects_created': objects_created,
            'html_links': html_links,
            'direct_html_link_index': 0,
            'file_links': file_links,
            'workspace_id': params['workspace_id'],
            'html_window_height': Var.report_height, 
        }

        # testing
        Var.params_report = params_report

        report_obj = Var.kbr.create_extended_report(params_report)

        output = {
            'report_name': report_obj['name'],
            'report_ref': report_obj['ref'],
        }

        #END run_classify

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_classify return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
