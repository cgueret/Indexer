'''
Created on 8 May 2016

@author: guerec01
'''
import os
import component
import logging
import requests
import json
from rdflib.plugins.stores import sparqlstore
from rdflib.graph import Graph, ConjunctiveGraph
from rdflib.namespace import Namespace
logger = logging.getLogger(__name__)

INDEXER = Namespace("http://example.org/indexer#")

class EntityExtractor(object):
    '''
    The entity extractor uses a set of processing rules to extract recognised
    entities from an RDF graph. The rules are defined as a set of CONSTRUCT
    queries which are all executed in order to get a set of entities.
    '''
    DB_NAME = 'reasoning'
    
    def __init__(self, store_url='http://localhost:5820/'):
        '''
        Constructor
        
        @param store_url: the URL of the triple store, 
        by default 'http://localhost:5820/'
        '''
        # Open the connection with the triple store
        query_url = store_url + self.DB_NAME + '/query'
        update_url = store_url + self.DB_NAME + '/update'
        self._store = sparqlstore.SPARQLUpdateStore(queryEndpoint=query_url, 
                                                   update_endpoint=update_url)

        # Load the rule base into memory and keep them as NT
        rules_base = os.path.join(component.__path__[0], 'rulebase.ttl')
        self._rules = Graph().parse(rules_base, format="turtle").serialize(format="nt").decode()
        
        # Initialise the database used for reasoning
        self._init_db(store_url)
        
    def _init_db(self, store_url):
        '''
        Initialise the database used for reasoning over an input graph
        and extract entities
        '''
        # Get the list of DBs and check if our DB is already there
        # if it is there just delete it
        response = requests.get(store_url + 'admin/databases')
        databases = json.loads(response.content.decode())['databases']
        if self.DB_NAME in databases:
            requests.delete(store_url + 'admin/databases/' + self.DB_NAME)
        
        # Parameters for the reasoning DB
        # more options http://docs.stardog.com/#_database_admin
        parameters = {"dbname" : self.DB_NAME,
                      "options" : {"search.enabled" : False, 
                                   "query.all.graphs": True,
                                   "index.type": "memory"},
                      "files": []
                      }
        files = {'data': ('data', json.dumps(parameters), 'application/json')}

        # Create the DB
        response = requests.post(store_url + 'admin/databases', files=files)
        if response.status_code == 201:
            logger.info('Created DB \"{}\"'.format(self.DB_NAME))
        else:
            logger.error('Could not create \"{}\"'.format(self.DB_NAME))
            logger.error(response.content.decode())
        
    def extract_entities(self, input_graph):
        '''
        Execute all the processing rules against the graph passed as parameter
        and return them as an array of graph. Each graph is a potential new
        proxy
        
        @param input_graph: the data graph to process in search for entities
        '''
        # Graph containing the data to process and the one containing the
        graph = ConjunctiveGraph(self._store)
        graph.update("DELETE { ?s ?p ?o } WHERE { ?s ?p ?o }")
        
        # Push the data and the the rules to the store
        graph.update("INSERT DATA { %s } " % self._rules)
        logger.debug(len(graph))
        graph.update("INSERT DATA { %s } " % input_graph.serialize(format='nt').decode())
        logger.debug(len(graph))
        
        for st in graph.triples((None, INDEXER.triggered, None)):
            logger.debug(st)
            
        results = []
        return results
