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

from .util.params import Params
from .util.report import HTMLReportWriter
from .util.dprint import dprint
from .util.config import reset_Var, Var
from .util.kbase_obj import  AmpliconMatrix, AttributeMapping
from .util.error import *




def run_check(cmd: str, shell=True):
    logging.info('Running cmd `%s`' % cmd)
    t0 = time.time() 
    
    # TODO remove shell for user-supplied?
    completed_proc = subprocess.run(cmd, shell=shell, executable='/bin/bash', stdout=sys.stdout, stderr=sys.stderr)

    logging.info('Took %.2fmin' % ((time.time() - t0)/60))

    if completed_proc.returncode != 0:
        raise NonZeroReturnException(
            "Command `%s` exited with non-zero return code `%d`. "
            "Check logs for more details" %
            (cmd, completed_proc.returncode)
        )


def prep_refdata():
    refdata_dir = '/kb/module/data'
    refdata_name = 'SILVA_138_SSU_NR_99'

    cmd = (
        'cd %s && cat %s_* > rejoined && tar xzf rejoined'
        % (refdata_dir, refdata_name)
    )

    run_check(cmd)

    if not os.path.exists(Var.propfile['silva_138_ssu']):
        raise Exception(cmd)



def parse_filterByConf(filterByConf_flpth: str, pad_ranks=True) -> dict:

    NUM_RANKS = 7
    
    # index is amplicon id
    df = pd.read_csv(filterByConf_flpth, sep='\t', index_col=0)
    id2taxStr_d = df.apply(
        lambda row: ';'.join(
            list(row.array) + ([''] * (NUM_RANKS - len(row.array)) if pad_ranks is True else []) 
        ), 
        axis=1
    ).to_dict()

    return id2taxStr_d


def parse_shortSeq(shortSeq_flpth: str):

    with open(shortSeq_flpth) as fh:
        ids = [id.strip() for id in fh.read().strip().splitlines() if len(id.strip()) > 0]

    return ids




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
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

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

        logging.info('Running `run_classify` with params:\n`%s`' % json.dumps(params, indent=3))


        #
        ##
        ### params
        ####
        #####

        params = Params(params)

        dprint('params', run=locals())


        #
        ##
        ### globals, directories, refdata, etc
        ####
        #####

        '''
        tmp/                                        `shared_folder`
        └── kb_rdp_cls_<uuid>/                      `run_dir`
            ├── return/                             `return_dir`
            |   ├── cmd.txt
            |   ├── study_seqs.fna
            |   └── RDP_Classifier_output/          `out_dir`
            |       ├── out_filterByConf.tsv
            |       └── out_fixedRank.tsv
            └── report/                             `report_dir`
                ├── fig
                |   ├── histogram.png
                |   ├── pie.png
                |   └── sunburst.png
                ├── histogram_plotly.html
                ├── pie_plotly.html
                ├── suburst_plotly.html
                └── report.html
        '''

        ##
        ## set up globals ds `Var` for this API-method run
        ## which involves making this API-method run's directory structure

        reset_Var() # clear all fields but `debug` and config stuff
        Var.update({
            'params': params,
            'run_dir': os.path.join(self.shared_folder, 'kb_rdp_cls_' + str(uuid.uuid4())),
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
        if params.is_custom():
            prep_refdata()


        #
        ##
        ### load objects
        ####
        #####

        amp_mat = AmpliconMatrix(params['amp_mat_upa'])

        row_attr_map_upa = amp_mat.obj.get('row_attributemapping_ref')
        if row_attr_map_upa is None:
            msg = (
                "Input AmpliconMatrix does not have a row AttributeMapping to assign traits to. "
                "A new row AttributeMapping will be created"
            )
            logging.warning(msg)
            Var.warnings.append(msg)

            # create new row AttributeMapping object 
            # from amp_mat.obj['data']['row_ids']
            # and row_mapping in amp_mat.obj['row_mapping']
            row_attr_map = AttributeMapping(row_attr_map_upa, amp_mat=amp_mat)  


        #
        ##
        ### cmd
        ####
        #####

        fasta_flpth = os.path.join(Var.return_dir, 'study_seqs.fna')
        cmd_flpth = os.path.join(Var.return_dir, 'cmd.txt')
        out_filterByConf_flpth = os.path.join(Var.out_dir, 'out_filterByConf.tsv')
        out_fixRank_flpth = os.path.join(Var.out_dir, 'out_fixRank.tsv')
        out_shortSeq_flpth = os.path.join(Var.out_dir, 'out_unclassifiedShortSeqs.txt') # seqs too short to classify

        shutil.copyfile(amp_mat.get_fasta(), fasta_flpth)

        cmd = (  
            'java -Xmx2g -jar %s classify %s ' # custom trained propfiles need bit more memory
            % (Var.classifier_jar_flpth, fasta_flpth) 
            + ' '.join(params.cli_args)
        )
        
        cmd_fixRank_shortSeq = cmd + ' --format filterByConf --outputFile %s --shortseq_outfile %s' % (out_filterByConf_flpth, out_shortSeq_flpth)
        cmd_filterByConf = cmd + ' --format fixRank --outputFile %s' % out_fixRank_flpth


        with open(cmd_flpth, 'w') as fh:
            fh.write(cmd_fixRank_shortSeq + '\n')
            fh.write(cmd_filterByConf + '\n')

        run_check(cmd_fixRank_shortSeq)
        run_check(cmd_filterByConf)



        #
        ##
        ### extract classifications
        ####
        #####

        id2taxStr_d = parse_filterByConf(out_filterByConf_flpth) 

        # get ids of classified and unclassified seqs
        shortSeq_id_l = parse_shortSeq(out_shortSeq_flpth) # sequences too short to get clsf
        classified_id_l = list(id2taxStr_d.keys())

        # make sure classifieds and shorts complement
        if Var.debug:
            assert sorted(classified_id_l + shortSeq_id_l) == sorted(amp_mat.obj['data']['row_ids'])

        # warnings
        if len(shortSeq_id_l) > 0:
            msg = (
                'One or more sequences are too short to be classified. '
                'See returned .zip for details')
            logging.warning(msg)
            Var.warnings.append(msg)

        # add in id->'' for unclassified seqs
        # so id2taxStr_l is complete
        # so no KeyErrors later
        for shortSeq_id in shortSeq_id_l:
            id2taxStr_d[shortSeq_id] = ''

        # add to globals for testing
        Var.shortSeq_id_l = shortSeq_id_l


        #
        ##
        ### add to row AttributeMapping
        ####
        #####

        attribute = (
            'RDP Classifier taxonomy, conf=%s, gene=%s, minWords=%s' 
            % (params.prose_args['conf'], params.prose_args['gene'], params.prose_args['minWords'])
        )
        source = 'kb_rdp_classifier/run_classify' # ver from provenance

        ind = row_attr_map.get_attribute_slot_warn(attribute, source)
        row_attr_map.update_attribute(ind, id2taxStr_d)


        #
        ##
        ### save obj
        ####
        #####

        row_attr_map_upa_new = row_attr_map.save()

        amp_mat.obj['row_attributemapping_ref'] = row_attr_map_upa_new
        amp_mat_upa_new = amp_mat.save()

        objects_created = [
            {'ref': row_attr_map_upa_new, 'description': 'Added or updated attribute `%s`' % attribute},
            {'ref': amp_mat_upa_new, 'description': 'Updated row AttributeMapping reference'},
        ]


        # testing
        Var.update(dict(
            amp_mat=amp_mat,
            row_attr_map=row_attr_map,
        ))




        #
        ##
        ### html report
        ####
        #####

        hrw = HTMLReportWriter(
            out_files=[out_fixRank_flpth, out_filterByConf_flpth], 
            cmd_l=[cmd_fixRank_shortSeq, cmd_filterByConf]
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
            'workspace_name': params['workspace_name'],
        }

        report = Var.kbr.create_extended_report(params_report)

        output = {
            'report_name': report['name'],
            'report_ref': report['ref'],
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
