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
    # Flattened params
    * `[]` access to required params (e.g., essential UPAs, workspace stuff)
    * `get`-like access to default-backed params ( e.g., 3rd-party tool params with defaults)
    * RDP Clsf params in prose mode
    * RDP Clsf params in CLI args mode

    You can leave off non-default params, like you would with underlying CLI tools
    However, if you do pass something in for a param, it has to be valid.

    Use `params.getd` for default-backed params

    Also the parameter groups are an effect of the app cell ui, 
    and params will be flattened right away
    '''

    DEFAULTS = {
       'output_name': None, # null case
       'conf': 0.8,                 
       'gene': '16srrna',           
       'minWords': None, # null case
       'write_ampset_taxonomy': 'do_not_overwrite' 
    }




    def __init__(self, params):

        ## Flatten right away##
        params = flatten(params)

        ## Validation
        self._validate(params)

        
        ## Custom transformations to internal state ##

        if 'output_name' in params and params['output_name'] == '':
            params['output_name'] = None # treat empty string as null case
                                         # since ui only returns strings for string type
        
        self.params = params


    def _validate(self, params):
        # TODO
        # don't allow extraneous params prevent misspelling
        pass


    @property
    def rdp_prose(self):
        '''
        For printing all RDP Clsf params to user in a pretty way
        '''

        return {
            'conf': '%g' % self.getd('conf'),
            'gene': self.getd('gene'),
            'minWords': 'default' if self.getd('minWords') is None else str(self.getd('minWords')),
        }


 
    @property
    def cli_args(self) -> list:
        '''
        Non-default RDP Classifier `classify` CLI args
        '''
       
        rdp_params = ['conf', 'gene', 'minWords'] # params for the RDP Clsf program

        # gather non-default
        cli_args = []
        for p in rdp_params:
            if self.getd(p) != self.DEFAULTS[p]:
                cli_args.append('--' + p)
                cli_args.append(str(self.params[p])) 

        return cli_args

    def __getitem__(self, key):
        '''
        For required params (e.g., input UPAs, workspace stuff)
        Should not use this for default-backed params
        as those can be left off params
        so use `getd` for those
        '''
        return self.params[key]

    def getd(self, key):
        '''
        Like `get`
        Return the user-supplied value, or the default value if none was supplied, or None if no default value
        '''
        return self.params.get(key, self.DEFAULTS.get(key))


    def __repr__(self):
        return 'Wrapper for params:\n%s' % (json.dumps(self.params, indent=4))
