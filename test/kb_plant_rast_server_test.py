# -*- coding: utf-8 -*-
import unittest
import os  # noqa: F401
import json  # noqa: F401
import time
import requests
import shutil

from os import environ
try:
    from ConfigParser import ConfigParser  # py2
except:
    from configparser import ConfigParser  # py3

from pprint import pprint  # noqa: F401

from biokbase.workspace.client import Workspace as workspaceService
from kb_plant_rast.kb_plant_rastImpl import kb_plant_rast
from GenomeFileUtil.GenomeFileUtilClient import GenomeFileUtil
from kb_plant_rast.kb_plant_rastServer import MethodContext
from kb_plant_rast.authclient import KBaseAuth as _KBaseAuth


class kb_plant_rastTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = environ.get('KB_AUTH_TOKEN', None)
        config_file = environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('kb_plant_rast'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'kb_plant_rast',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = workspaceService(cls.wsURL)
        cls.serviceImpl = kb_plant_rast(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']
        cls.gfu = GenomeFileUtil(cls.callback_url)
        cls.genome = "Test_Genome"
        cls.prepare_data()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    def getWsClient(self):
        return self.__class__.wsClient

    def getWsName(self):
        if hasattr(self.__class__, 'wsName'):
            return self.__class__.wsName
        suffix = int(time.time() * 1000)
        wsName = "test_kb_plant_rast_" + str(suffix)
        ret = self.getWsClient().create_workspace({'workspace': wsName})  # noqa
        self.__class__.wsName = wsName
        return wsName

    def getImpl(self):
        return self.__class__.serviceImpl

    def getContext(self):
        return self.__class__.ctx

    @classmethod
    def prepare_data(cls):
        cls.gff_filename = 'Test_v1.0.gene.gff3.gz'
        cls.gff_path = os.path.join(cls.scratch, cls.gff_filename)
        shutil.copy(os.path.join("/kb", "module", "data", cls.gff_filename), cls.gff_path)

        cls.fa_filename = 'Test_v1.0.fa.gz'
        cls.fa_path = os.path.join(cls.scratch, cls.fa_filename)
        shutil.copy(os.path.join("/kb", "module", "data", cls.fa_filename), cls.fa_path)

    def loadFakeGenome(cls):
        
        input_params = {
            'fasta_file': {'path': cls.fa_path},
            'gff_file': {'path': cls.gff_path},
            'genome_name': cls.genome,
            'workspace_name': cls.getWsName(),
            'source': 'Phytozome',
            'type': 'Reference',
            'scientific_name': 'Populus trichocarpa'
        }

        result = cls.gfu.fasta_gff_to_genome(input_params)

    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    def test_plant_rast(self):
        print "Testing Plant RAST"

        #Load Fake Genome
        self.loadFakeGenome()

        # Copying Plant Genome
        #Test_Genome = 'Fvesca_PhytozomeV11_v1.1'
        #self.getWsClient().copy_object({'from':{'workspace':'Phytozome_Genomes','name':Test_Genome},
        #                                'to':{'workspace': self.getWsName(),'name':Test_Genome}})

        # Running Plant RAST
        ret = self.getImpl().annotate_plant_transcripts(self.getContext(), {'input_ws' : self.getWsName(),
                                                                            'input_genome' : self.genome })

        print ret[0]
        self.assertEqual(ret[0]['ftrs'],1028)
        self.assertEqual(ret[0]['fns'],512)
        self.assertEqual(ret[0]['hit_ftrs'],37)
        self.assertEqual(ret[0]['hit_fns'],26)
