# -*- coding: utf-8 -*-
#BEGIN_HEADER
import os
import uuid

from KBaseReport.KBaseReportClient import KBaseReport
from GenomeFileUtil.GenomeFileUtilClient import GenomeFileUtil
from DataFileUtil.DataFileUtilClient import DataFileUtil
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
    KMER_THRESHOLD = 1
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.workspaceURL = config['workspace-url']
        self.token = os.environ['KB_AUTH_TOKEN']
        self.scratch = os.path.abspath(config['scratch'])
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.dfu = DataFileUtil(self.callback_url)
        self.gfu = GenomeFileUtil(self.callback_url)
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
        
        # Retrieve plant genome
        plant_genome = self.dfu.get_objects({'object_refs': [input['input_ws']+'/'+input['input_genome']]})['data'][0]
        features = plant_genome['data']['cdss']
        if(len(features)==0):
            features = plant_genome['data']['features']
            if(len(features)==0):
                raise Exception("The genome does not contain any CDSs or features!")

        output = {'ftrs': len(features)}

        # Retrieve kmers
        Functions = set()
        Kmers_Functions = dict()
        for line in open('/data/functions_kmers.txt'):
            line=line.strip()
            (function_string,kmers_string)=line.split('\t')
            Functions.add(function_string)
            for kmer in kmers_string.split(', '):
                Kmers_Functions[kmer]=function_string
        output['fns']=len(Functions)
        output['kmers']=len(Kmers_Functions)

        Kmer_Length=8
        Hit_Proteins=dict()
        Hit_Kmers=set()
        output['short']=0
        for ftr in features:
            if('protein_translation' not in ftr):
                output['short']+=1
                continue

            Seq = ftr['protein_translation']
            SeqLen = len(Seq);
            if(SeqLen < 10):
                output['short']+=1
                continue
            seq_kmers = [Seq[i:i + Kmer_Length] for i in range(SeqLen-Kmer_Length+1)]
            for kmer in seq_kmers:
                if(kmer in Kmers_Functions):
                    if(ftr['id'] not in Hit_Proteins):
                        Hit_Proteins[ftr['id']]=dict()
                    if(Kmers_Functions[kmer] not in Hit_Proteins[ftr['id']]):
                        Hit_Proteins[ftr['id']][Kmers_Functions[kmer]]=0
                    Hit_Proteins[ftr['id']][Kmers_Functions[kmer]]+=1
                    Hit_Kmers.add(kmer)
        output['hit_kmers']=len(Hit_Kmers)

        #Eliminate hits that have a small number of kmers
        #Each function must have more than 1 kmer in order to be assigned
        Deleted_Proteins = set()
        output['few']=0
        for ftr in Hit_Proteins.keys():
            Deleted_Functions = set()
            for function in Hit_Proteins[ftr].keys():
                N_Kmers = Hit_Proteins[ftr][function]
                if(N_Kmers <= self.KMER_THRESHOLD):
                    Deleted_Functions.add(function)
                
            for function in Deleted_Functions:
                del(Hit_Proteins[ftr][function])
                
            if(len(Hit_Proteins[ftr])==0):
                output['few']+=1
                Deleted_Proteins.add(ftr)

        #Scan for multi-functional hits
        #If a function has more hits than others, it takes precendence
        #If there are more than one function with an equal number of hits, the feature is removed
        output['ambiguous']=0
        for ftr in Hit_Proteins:
            if(len(Hit_Proteins[ftr])==1):
                continue

            if(ftr in Deleted_Proteins):
                continue

            Top_Hit_Functions=dict()
            for function in Hit_Proteins[ftr].keys():
                if(Hit_Proteins[ftr][function] not in Top_Hit_Functions):
                    Top_Hit_Functions[Hit_Proteins[ftr][function]]=dict()
                Top_Hit_Functions[Hit_Proteins[ftr][function]][function]=1

            Top_Number = (sorted(Top_Hit_Functions.keys(),reverse=True))[0]
            if(len(Top_Hit_Functions[Top_Number].keys())>1):
                output['ambiguous']+=1
                Deleted_Proteins.add(ftr)
            else:
                Top_Function = Top_Hit_Functions[Top_Number].keys()[0]
                Hit_Proteins[ftr]={Top_Function:Top_Number}
            
        #remove the egregious proteins
        for ftr in Deleted_Proteins:
            del(Hit_Proteins[ftr])

        #count functions
        Hit_Functions=set()
        for ftr in Hit_Proteins.keys():
            Hit_Functions.add(Hit_Proteins[ftr].keys()[0])

        output['hit_ftrs']=len(Hit_Proteins)
        output['hit_fns']=len(Hit_Functions)

        #Now, re-populate feature functions, and save genome object
        for ftr in features:
            if(ftr['id'] in Hit_Proteins):
                if('function' in ftr):
                    old_function = ftr['function']
                ftr['function'] = Hit_Proteins[ftr['id']].keys()[0]
        
        if('output_genome' not in input):
            input['output_genome']=input['input_genome']

        save_result = self.gfu.save_one_genome({'workspace' : input['input_ws'],
                                                'name' : input['output_genome'],
                                                'data' : plant_genome['data']});

        html_string="<html><head><title>KBase Plant Rast Report</title></head><body>"
        html_string+="<p>The Plant Rast app has finished running.</p>"
        html_string+="<p>"+str(output['ftrs'])+" features were scanned with "+str(output['kmers'])+" signature kmers "
        html_string+="representing "+str(output['fns'])+" PlantSEED metabolic functions. "
        html_string+="The app detected "+str(output['hit_kmers'])+" signature kmers representing "
        html_string+=str(output['hit_fns'])+" functions in "+str(output['hit_ftrs'])+" features.</p>"
        html_string+="<p>During the annotation process, "+str(output['short'])+" features "
        html_string+="were ignored because they were too short (<10 AA in length). "
        html_string+=str(output['few'])+" features were ignored because they were hit by fewer than 2 kmers, and "
        html_string+=str(output['ambiguous'])+" features were ignored because they were too ambiguous "
        html_string+="(connected to multiple distinct metabolic functions).</p>"
        fraction_plantseed = float(output['hit_fns']) / float(output['fns'])
        html_string+="<p>This result indicates that {0:.2f} of the primary metabolism curated as part ".format(fraction_plantseed)
        html_string+="of the PlantSEED project was detected in the set of features.</p></body>"

        saved_genome = "{}/{}/{}".format(save_result['info'][6],save_result['info'][0],save_result['info'][4])
        description = "Plant genome "+plant_genome['data']['id']+" annotated with metabolic functions"
        uuid_string = str(uuid.uuid4())
        report_params = { 'objects_created' : \
                          [{"ref":saved_genome,"description":description}],
                          'direct_html' : html_string,
                          'workspace_name' : input['input_ws'],
                          'report_object_name' : 'kb_plant_rast_report_' + uuid_string }
        kbase_report_client = KBaseReport(self.callback_url, token=self.token)
        report_client_output = kbase_report_client.create_extended_report(report_params)
        output['report_name']=report_client_output['name']
        output['report_ref']=report_client_output['ref']

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
