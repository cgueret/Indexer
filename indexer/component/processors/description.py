'''
Created on 8 May 2016

@author: guerec01
'''
import requests
import json
from rdflib.plugins.stores import sparqlstore
from rdflib.graph import Graph
from rdflib.namespace import Namespace, RDF
from rdflib.plugins.sparql.processor import prepareQuery

import logging
logger = logging.getLogger(__name__)

class DescriptionExtractor(object):
    '''
    The entity extractor uses a set of processing rules to extract recognised
    entities from an RDF graph. The rules are defined as a set of CONSTRUCT
    queries which are all executed in order to get a set of entities.
    '''
    DB_NAME = 'reasoning'
    
    def __init__(self, config):
        '''
        Constructor
        
        @param config: The configuration object
        '''
        self.store_url = config.stardog_url()
                                    
        # Open the connection with the triple store
        query_url = config.stardog_url() + config.stardog_db() + '/query'
        update_url = config.stardog_url() + config.stardog_db() + '/update'
        self._store = sparqlstore.SPARQLUpdateStore(queryEndpoint=query_url,
                                                   update_endpoint=update_url)

        
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