# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os
import sys
import uuid
import subprocess
import functools

from installed_clients.WorkspaceClient import Workspace
from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.KBaseReportClient import KBaseReport

from .util.report import HTMLReportWriter
from .util.dprint import dprint
from .util.config import reset, _globals
from .util.kbase_obj import AmpliconSet, AmpliconMatrix, AttributeMapping
from .util.error import *
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

        callback_url = os.environ['SDK_CALLBACK_URL']
        workspace_url = config['workspace-url']
        shared_folder = config['scratch']
        
        self._globals = { # shared by all API-method runs (?)
            'callback_url': callback_url,
            'shared_folder': config['scratch'], 
            'ws': Workspace(workspace_url),
            'dfu': DataFileUtil(callback_url),
            'kbr': KBaseReport(callback_url),
            }

        #END_CONSTRUCTOR
        pass


    def classify(self, ctx, params):
        """
        This example function accepts any number of parameters and returns results in a KBaseReport
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN classify



        dprint('params', run=locals()) # TODO validate `params`
                                       # TODO ui option to append to name?


        # set up globals ds `_globals` for this API-method run

        reset(_globals) # clear all fields but `debug`
        _globals.update({
            **self._globals,
            'params': params,
            'run_dir': os.path.join(self._globals['shared_folder'], str(uuid.uuid4())),
            'warnings': [],
            'classifierJar_flpth': '/opt/rdp_classifier_2.12/dist/classifier.jar',
            })

        os.mkdir(_globals.run_dir)




        #
        ##
        ### load objects
        ####
        #####


        if _globals.debug and params.get('skip_obj'):
            dprint('Skip obj - loading objects')
        
        else:
            # input object, which has the amplicons
            amp_set = AmpliconSet(params['amplicon_set_upa'], mini_data=params.get('mini_data'))
            amp_set.to_fasta()

            # intermediate referenced
            amp_mat = AmpliconMatrix(amp_set.amp_mat_upa)

            # if `row_attrmap_upa` == None, 
            # create new row AttributeMapping object 
            # from amp_mat.obj['data']['row_ids']
            row_attrmap = AttributeMapping(upa=amp_mat.row_attrmap_upa, amp_mat=amp_mat)  

            dprint('params["amplicon_set_upa"]', 'amp_set.amp_mat_upa', 'amp_mat.row_attrmap_upa', run=locals())




        #
        ##
        ### params
        ####
        #####


        defaults = {
            'conf': 0.8,
            'gene': '16srrna',
            'minWords': None,
        }

        params_rdp = params.get('rdp_classifier', defaults)

        params_rdp_prose = { # for printing
            'conf': '%.2f' % params_rdp.get('conf', defaults['conf']),
            'gene': params_rdp.get('gene', defaults['gene']),
            'minWords': str(params_rdp.get('minWords', 'default')),
        }

        cmd_params = []
        for key, value in defaults.items():
            if key in params_rdp and params_rdp[key] != value:
                cmd_params.append('--' + key + ' ' + str(params_rdp[key]))


        dprint('cmd_params', run=locals())


        #
        ##
        ### cmd
        ####
        #####

        out_filterByConf_flpth = os.path.join(_globals.run_dir, 'out_filterByConf.tsv')
        out_fixRank_flpth = os.path.join(_globals.run_dir, 'out_fixRank.tsv')


        if _globals.debug and params.get('skip_run'):
            dprint('Skipping run')
            dprint(f'cp /kb/module/test/data/* {_globals.run_dir}', run='cli')

            cmd_fixRank = 'Skip'
            cmd_filterByConf = 'Skip'


        else:
          
            cmd_base = 'java -Xmx1g -jar %s classify %s ' % (_globals.classifierJar_flpth, 
                amp_set.fasta_flpth) + ' '.join(cmd_params)
            
            cmd_fixRank = cmd_base + ' --format filterByConf --outputFile %s' % out_filterByConf_flpth
            cmd_filterByConf = cmd_base + ' --format fixRank --outputFile %s' % out_fixRank_flpth





        #
        ##
        ### subproc
        ####
        #####


        if _globals.debug and params.get('skip_run'):
            logging.debug('Skip run')

        else:

            subproc_run = functools.partial( # TODO remove shell
                subprocess.run, shell=True, executable='/bin/bash', stdout=sys.stdout, stderr=sys.stderr)


            def run_check(cmd, subproc_run_kwargs={}):
                logging.info('Running cmd `%s`' % cmd)
                completed_proc = subproc_run(cmd, **subproc_run_kwargs)
                if completed_proc.returncode != 0:
                    raise NonZeroReturnException(
                        "Command: `%s` exited with non-zero return code: `%d`. "
                        "Check logs for more details" %
                        (cmd, completed_proc.returncode))


            run_check(cmd_fixRank)
            run_check(cmd_filterByConf)





        #
        ##
        ### add taxStr to AmpliconSet / row AttributeMapping
        ####
        #####

        source = 'kb_RDP_Classifier/classify'
        attribute = 'RDP Classifier Taxonomy, ' + \
            'conf=%s, gene=%s, minWords=%s' % (
            params_rdp_prose['conf'], params_rdp_prose['gene'], params_rdp_prose['minWords'])


        if _globals.debug and params.get('skip_obj'):
            logging.debug('Skip obj - add taxStr to AmpliconSet / row AttributeMapping')

        else:

            id2taxStr_d = AttributeMapping.parse_filterByConf(out_filterByConf_flpth) # TODO better place for this func

            dprint('id2taxStr_d', 'len(id2taxStr_d)', run=locals())

            ##
            ## AmpliconSet

            write_setting = params.get('write_amplicon_set_taxonomy', 'do_not_overwrite')
    
            if write_setting != 'do_not_write':
                amp_set.write_taxonomy(id2taxStr_d, write_setting=='overwrite')


            ##
            ## row AttributeMapping

            row_attrmap.add_attribute_slot(attribute)
            row_attrmap.update_attribute(id2taxStr_d, attribute, source)

            



        #
        ##
        ### update/save row AttributeMaping + referencing objects
        ####
        #####

        if _globals.debug and params.get('skip_obj'):
            dprint('Skip obj')
            objects_created = []

        else:

            row_attrmap_upa_new = row_attrmap.save()

            amp_mat.update_row_attributemapping_ref(row_attrmap_upa_new)
            amp_mat_upa_new = amp_mat.save()

            amp_set.update_amplicon_matrix_ref(amp_mat_upa_new)
            amp_set_upa_new = amp_set.save(name=params.get('output_name'))

            objects_created = [
                {'ref': row_attrmap_upa_new, 'description': 'Added or updated attribute `%s`' % attribute},
                {'ref': amp_mat_upa_new, 'description': 'Updated row AttributeMapping reference'},
                {'ref': amp_set_upa_new, 'description': 'Updated AmpliconMatrix reference'},
            ]







        #
        ##
        ### html report
        ####
        #####


        hrw = HTMLReportWriter(out_files=[out_fixRank_flpth, out_filterByConf_flpth], 
                            params_prose=params_rdp_prose,
                            cmd_l=[cmd_fixRank, cmd_filterByConf])

        report_dir, html_flpth = hrw.write()



        html_links = [{
            'path': report_dir,
            'name': os.path.basename(html_flpth),
            }]






        #
        ##
        ###
        ####
        #####

        file_links = [{
            'path': _globals.run_dir,
            'name': 'RDP_Classifier_results.zip',
            'description': 'Input, output'
            }]

        params_report = {
            'warnings': _globals.warnings,
            'objects_created': objects_created,
            'html_links': html_links,
            'direct_html_link_index': 0,
            'file_links': file_links,
            'workspace_name': params['workspace_name'],
            }

        if _globals.debug and params.get('return_testingInfo'):
            return {
                **params_report,
                'source': source,
                'attribute': attribute,
            }

        if _globals.debug and params.get('skip_objReport'):
            output = {}
        else:
            report = _globals.kbr.create_extended_report(params_report)
            output = {
                'report_name': report['name'],
                'report_ref': report['ref'],
            }

        #END classify

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method classify return value ' +
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
