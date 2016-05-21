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
from rdflib.graph import Graph
from rdflib.namespace import Namespace, RDF
from rdflib.plugins.sparql.processor import prepareQuery
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

        # Load the rule base into memory
        self._rules = {}
        rules_base = os.path.join(component.__path__[0], 'rulebase.ttl')
        logger.debug('Loading {}'.format(rules_base))
        g = Graph().parse(rules_base, format="turtle")
        for s in g.subjects(RDF.type, INDEXER.Rule):
            q = prepareQuery(g.value(s, INDEXER.content).toPython())
            self._rules[s.toPython()] = q
        logger.info('Loaded {} rule(s)'.format(len(self._rules)))
        
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
        # The results as an array of generated graphs
        results = []
        
        # Apply all the rules one by one
        for (name, rule) in self._rules.items():
            graph = input_graph.query(rule).graph
            if len(graph) != 0:
                logger.debug('Found a match for {}'.format(name))
                results.append(graph)
                
        return results
