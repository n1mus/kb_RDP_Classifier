import json




def flatten(d):
    '''
    At most 1 level nesting
    '''
    d1 = d.copy()
    for k, v in d.items():
        if isinstance(v, dict):
            for k1, v1 in d1.pop(k).items():
                d1[k1] = v1
    return d1



class Params:
    '''
    Provides interface for:
    -----------------------
    * `[]` and `get` access to flattened params, 
      with app/user-specified/`None` default (in that order)
    * RDP Clsf params in prose mode
    * RDP Clsf params in CLI args mode

    '''

    PARAMS_DEFAULT = {
       'output_name': None,             # optional
       'rdp_clsf': {                    # optional
           'conf': 0.8,                 # optional
           'gene': '16srrna',           # optional
           'minWords': None,            # optional
       },
       'write_ampset_taxonomy': 'do_not_overwrite' # optional
    }

    FLATPARAMS_DEFAULT = flatten(PARAMS_DEFAULT)

    CUSTOM_GENES = ['SILVA_138_SSU_NR_99', 'SILVA_138_SSU_NR_99_NCBI_taxonomy']



    def __init__(self, params):

        # TODO validation

        ##
        ## custom transformations
        if 'output_name' in params and params['output_name'] == '':
            params['output_name'] = None # treat empty string as null case
                                         # since ui only returns strings for string type

        ##
        ##
        self.params = params
        self.flatParams = flatten(params)


        ##
        ##
        if self.clsf_with_trained:
            raise NotImplementedError('Classifying against custom datasets not ready')


    def _validate(self):
        pass




    @property
    def clsf_with_trained(self):
        return self.get('gene') in self.CUSTOM_GENES



    @property
    def rdp_prose(self):
        '''For printing to user'''

        return {
            'conf': '%g' % self.get('conf'),
            'gene': self.get('gene'),
            'minWords': 'default' if self.get('minWords') is None else self.get('minWords'),
        }


 
    @property
    def cli_args(self) -> list:
        '''
        Non-default RDP Classifier `classify` cli args
        '''
       
        defaults = self.PARAMS_DEFAULT['rdp_clsf']
        params_rdp = self.params.get('rdp_clsf', dict())

        # gather non-default rdp params
        cli_args = []
        for key, value in defaults.items(): # TODO account for custom propfile
            if key in params_rdp and params_rdp[key] != value:
                cli_args.append('--' + key)
                cli_args.append(str(params_rdp[key])) 

        return cli_args

    def __contains__(self, key):
        return key in self.flatParams

    def __getitem__(self, key):
        return self.flatParams[key]



    def get(self, key, default=None):
        '''
        Generally,
        return value, app default, user-specified default, or None, in that order

        Does other considerations for
        * `output_name`
        '''
        if key in self.flatParams:
            return self.flatParams[key]
        
        if key in self.FLATPARAMS_DEFAULT:
            return self.FLATPARAMS_DEFAULT[key]

        return default


    def __repr__(self):
        return 'Wrapper for params\n%s' % (json.dumps(self.params, indent=4))
