# -*- coding: utf-8 -*-
#BEGIN_HEADER
import os
from KBaseReport.KBaseReportClient import KBaseReport
from Workspace.WorkspaceClient import Workspace as workspaceService
#END_HEADER


class kb_plant_rast:
    '''
    Module Name:
    kb_plant_rast

    Module Description:
    A KBase module: kb_plant_rast
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = "https://github.com/kbaseapps/kb_plant_rast"
    GIT_COMMIT_HASH = "a652c0120abf90e97d0f0214f8ed4174f27b9a09"

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.workspaceURL = config['workspace-url']
        self.scratch = os.path.abspath(config['scratch'])
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        #END_CONSTRUCTOR
        pass


    def annotate_plant_transcripts(self, ctx, input):
        """
        :param input: instance of type "AnnotatePlantTranscriptsParams" ->
           structure: parameter "input_ws" of String, parameter
           "input_genome" of String, parameter "output_genome" of String
        :returns: instance of type "AnnotatePlantTranscriptsResults" ->
           structure: parameter "report_name" of String, parameter
           "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN annotate_plant_transcripts

        token = ctx['token']
        wsClient = workspaceService(self.workspaceURL, token=token)

        # Retrieve plant genome
        plant_genome = wsClient.get_objects2({'objects': [{'ref' : input['input_ws']+'/'+input['input_genome']}]})['data'][0]
        output = {'ftrs': len(plant_genome['data']['features'])}

        # Retrieve kmers
        Functions = {}
        Kmers_Functions = {}
        for line in open('/kb/module/data/functions_kmers.txt'):
            line=line.strip()
            (function_string,kmers_string)=line.split('\t')
            Functions[function_string]=1
            for kmer in kmers_string.split(', '):
                Kmers_Functions[kmer]=function_string
        output['fns']=len(Functions.keys())

        Kmer_Length=8
        Hit_Proteins={}
        output['skipped']=0
        for ftr in plant_genome['data']['features']:
            Seq = ftr['protein_translation']
            SeqLen = len(Seq);
            if(SeqLen < 10):
                output['skipped']+=1
                continue
            seq_kmers = [Seq[i:i + Kmer_Length] for i in range(SeqLen-Kmer_Length+1)]
            for kmer in seq_kmers:
                if(kmer in Kmers_Functions):
                    if(ftr['id'] not in Hit_Proteins):
                        Hit_Proteins[ftr['id']]={}
                    if(Kmers_Functions[kmer] not in Hit_Proteins[ftr['id']]):
                        Hit_Proteins[ftr['id']][Kmers_Functions[kmer]]=0
                    Hit_Proteins[ftr['id']][Kmers_Functions[kmer]]+=1

        #Scan for multi-functional hits
        #If a function has more hits than others, it takes precendence
        #If there are more than one function with an equal number of hits, the feature is removed
        Delete_Proteins={}
        for ftr in Hit_Proteins.keys():
            if(len(Hit_Proteins[ftr])==1):
                continue
            
            Top_Hit_Functions={}
            for function in Hit_Proteins[ftr].keys():
                if(Hit_Proteins[ftr][function] not in Top_Hit_Functions):
                    Top_Hit_Functions[Hit_Proteins[ftr][function]]={}
                Top_Hit_Functions[Hit_Proteins[ftr][function]][function]=1

            Top_Number = (sorted(Top_Hit_Functions.keys(),reverse=True))[0]
            if(len(Top_Hit_Functions[Top_Number].keys())>1):
                # delete hit
                Delete_Proteins[ftr]=1
                pass
            else:
                Top_Function = Top_Hit_Functions[Top_Number].keys()[0]
                Hit_Proteins[ftr]={Top_Function:Top_Number}
            
        #remove the egregious proteins
        for ftr in Delete_Proteins.keys():
            del(Hit_Proteins[ftr])

        #count functions
        Hit_Functions={}
        for ftr in Hit_Proteins.keys():
            Hit_Functions[Hit_Proteins[ftr].keys()[0]]=1

        output['hit_ftrs']=len(Hit_Proteins.keys())
        output['hit_fns']=len(Hit_Functions.keys())

        #Now, re-populate feature functions, and save genome object
        for ftr in plant_genome['data']['features']:
            if(ftr['id'] in Hit_Proteins):
                if('function' in ftr):
                    old_function = ftr['function']
                ftr['function'] = Hit_Proteins[ftr['id']].keys()[0]
        
        if('output_genome' not in input):
            input['output_genome']=input['input_genome']

        save_result = wsClient.save_objects({'workspace':input['input_ws'],
                                             'objects': [{'name' : input['output_genome'],
                                                          'data' : plant_genome['data'],
                                                          'type' : "KBaseGenomes.Genome",
                                                          'meta' : plant_genome['info'][10]}]})

        #END annotate_plant_transcripts

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method annotate_plant_transcripts return value ' +
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
