#encoding: utf-8
'''
Created on 1 Apr 2016

@author: guerec01
'''
import uuid
from rdflib.namespace import OWL, RDF, RDFS
from indexer.util.namespaces import OLO
from rdflib.graph import Graph
from rdflib.term import URIRef, BNode, Literal
from SPARQLWrapper import SPARQLWrapper, JSON, POST

import logging
import requests
import json
logger = logging.getLogger(__name__)

class IndexStore(object):
    '''
    Interface to the store containing the data about the proxy entities, the
    collections and the audience
    '''

    def __init__(self, config):
        '''
        Constructor
        
        @param base: the base for all the minted URIs
        @param store: location of the triple store
        '''
        # The URIs for the store
        self.store_url = config.stardog_url()
        self.db_name = config.stardog_db()
        self.sparql = config.stardog_url() + config.stardog_db() + '/query'
        self.sparul = config.stardog_url() + config.stardog_db() + '/update'

        # The base for all the URIs
        self.base = config.base()
    
        # Get the list of DBs and check if our DB is already there
        response = requests.get(self.store_url + 'admin/databases')
        databases = json.loads(response.content.decode())['databases']
        
        # If not initialise it
        if not self.db_name in databases:
            self.reset_db()
            
    def reset_db(self):
        '''
        Initialise the database
        '''
        # Get the list of DBs and check if our DB is already there
        # if it is there just delete it
        response = requests.get(self.store_url + 'admin/databases')
        databases = json.loads(response.content.decode())['databases']
        if self.db_name in databases:
            requests.delete(self.store_url + 'admin/databases/' + self.db_name)
        
        # Parameters for the reasoning DB
        # more options http://docs.stardog.com/#_database_admin
        parameters = {"dbname" : self.db_name,
                      "options" : {"search.enabled" : True,
                                   "query.all.graphs": True,
                                   "index.type": "disk"},
                      "files": []}
        files = {'data': ('data', json.dumps(parameters), 'application/json')}

        # Create the DB
        response = requests.post(self.store_url + 'admin/databases', files=files)
        if response.status_code == 201:
            logger.info('Created DB \"{}\"'.format(self.db_name))
        else:
            logger.error('Could not create \"{}\"'.format(self.db_name))
            logger.error(response.content.decode())
        
    def store(self, dataset):
        '''
        Persist the given data set into the triple store. The data set is
        composed of several named graphs containing part of the proxy
        description. There is also supposed to be one graph with the provenance
        information. All the graphs are stored as-is eventually overwriting 
        previous content stored under the same graph name.
        
        @param dataset: the data set containing some proxy descriptions derived
        from processing a cached document
        
        @return: True if successful
        '''
        
        for graph in dataset.graphs():
            # Skip empty graphs
            if len(graph) == 0:
                continue
            
            # Get the name of the graph and its content
            graph_name = graph.identifier.toPython()
            payload = graph.serialize(format="nt").decode()
            
            # Store the graph
            # TODO Use rdflib tricks to optimise that part
            logger.info("Storing {} triples into <{}>".format(len(graph), graph_name))            
            query = """
                INSERT DATA { GRAPH <__NAME__> { __PAYLOAD__ } }
            """.replace("__PAYLOAD__", payload).replace("__NAME__", graph_name)
            sparql = SPARQLWrapper(self.sparul)
            sparql.setQuery(query)
            sparql.setMethod(POST)
            sparql.query()
        
        return True
    
    def has_proxy(self, uri):
        '''
        Returns True if there is a proxy entity containing this URI
        '''
        return self.get_proxy_uri(uri) != None
        
    def lookup(self, uri):
        '''
        Find a proxy referring to the given URI
        '''
        logger.info('Lookup {}'.format(uri))
        query = self._queries['find_proxy.rq'].replace("__TARGET__", uri)
        sparql = SPARQLWrapper(self.sparql)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        bindings = sparql.query().convert()["results"]["bindings"]
        if len(bindings) == 0:
            return None
        
        proxy = bindings[0]["proxy"]["value"]
        print ('Found the proxy {}'.format(proxy))
        return proxy
    
    def search(self, search_uri, params, collection='everything'):
        '''
        Full text search. The parameters are expected to contain a variable
        'q' with the text to be searched for.
        '''
        # Prepare the graph of results
        graph = Graph()
        graph.namespace_manager.bind('olo', OLO)
        
        # Prepare the query
        query = self._queries['full_text_search.rq']
        query = query.replace("__TEXT__", params.get('q'))
        query = query.replace("__COLLECTION__", self.base + collection)        
        logger.debug('Executing \n{}'.format(query))
        
        # Execute the query
        sparql = SPARQLWrapper(self.sparql)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        bindings = sparql.query().convert()["results"]["bindings"]
        
        # Build the OLO slots
        index = 0
        for b in bindings:
            # Increment the index
            index = index + 1
            
            # Get the minimal amount of information to describe a result
            result_uri = b["proxy"]["value"]
            label = b["label"]["value"]
            description = b["description"]["value"]
            
            # Create a result slot
            slot = BNode()
            graph.add((slot, RDF.type, OLO.Slot))
            graph.add((slot, RDFS.label, Literal("Result #{}".format(index+1))))
            graph.add((slot, OLO['index'], Literal(index+1)))
            graph.add((slot, OLO.item, URIRef(result_uri)))
            
            # Describe the result dataset
            graph.add((URIRef(search_uri), OLO.slot, slot))
 
            # Describe the result entry
            graph.add((URIRef(result_uri), RDFS.label, Literal(label)))
            graph.add((URIRef(result_uri), RDFS.comment, Literal(description)))
        
        # Add some text to describe the search    
        title = Literal("Everything containing \"{}\"".format(params['q']))
        graph.add((URIRef(search_uri), RDFS.label, title))
            
        return graph
    
    def get_proxy(self, uri):
        '''
        Returns the description of a proxy entity
        '''
        logger.info('Get proxy data about {}'.format(uri))
        query = self._queries['get_proxy.rq'].replace("__URI__", uri)
        sparql = SPARQLWrapper(self.sparql)
        sparql.setQuery(query)
        data = sparql.query().convert()
        return data
    
    def get_proxy_uri(self, uri):
        '''
        Returns the location of the proxy containing that URI
        '''
        # TODO Use rdflib tricks to optimise that part
        query = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT ?proxy WHERE { ?proxy owl:sameAs <__TARGET__>.}
        """.replace("__TARGET__", uri)
        sparql = SPARQLWrapper(self.sparql)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        bindings = sparql.query().convert()["results"]["bindings"]
        if len(bindings) > 0:
            return URIRef(bindings[0]["proxy"]["value"])
        else:
            return None
     
    def update_uris(self, replacement_map):
        '''
        This function takes as a parameter a set of mapping old->new for URIs.
        This is used to update references to a URI for which a proxy was not
        available at the time of processing but has been created afterwards.
        '''
        for (old_uri, new_uri) in replacement_map.items():
            logger.info("Update {} -> {}".format(old_uri, new_uri))
            query = """
                DELETE {?s ?p <OLD_URI>.}
                INSERT {?s ?p <NEW_URI>.}
                WHERE {?s ?p <OLD_URI>.}
                """.replace("OLD_URI", old_uri).replace("NEW_URI", new_uri)
            sparql = SPARQLWrapper(self.sparul)
            sparql.setQuery(query)
            sparql.setMethod(POST)
            sparql.query()
    
    def close(self):
        '''
        Close open connections 
        '''
        pass
