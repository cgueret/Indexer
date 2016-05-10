'''
Created on 1 Apr 2016

@author: guerec01
'''
import uuid
from rdflib.namespace import OWL
from rdflib.graph import Graph
from rdflib.term import URIRef
from SPARQLWrapper import SPARQLWrapper, JSON, POST
import storage
import os
from storage.config import BASE, SPARQL, SPARUL

import logging
logger = logging.getLogger(__name__)

class ProxyStore(object):
    '''
    Interface to the store containing the data about the proxy entities
    '''

    def __init__(self):
        '''
        Constructor
        '''
        # Map to store the queries as text blobs
        self._queries = {}
        
        # Load all the SPARQL queries
        path = os.path.join(storage.__path__[0], 'queries')
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            if os.path.isfile(full_path) and entry.split('.')[-1] == 'rq':
                logger.info('Loading {}'.format(entry))
                self._queries[entry] = open(full_path, 'r').read()
    
    def store(self, graph):
        '''
        Take the given graph and turn it into a proxy entity, or update the
        description of an existing proxy with the properties defined in the
        graph
        '''
        # Find the subject of the graph 
        subject = [s for s in graph.subjects()][0]
        
        # Check if we have a proxy or need to create a new one
        if self.has_proxy(subject):
            # There is already a proxy
            proxy_uri = self.get_proxy_uri(subject)
            created_proxy = False
        else:
            # Generate a new UUID
            logger.info("Generating a new proxy")
            proxy_uri = URIRef("{}{}#id".format(BASE, uuid.uuid1()))
            created_proxy = True

        #  Create a new graph that will be inserted at the end
        proxy_graph = Graph()
        
        # State that this entity is part of the proxy
        proxy_graph.add((proxy_uri, OWL.sameAs, subject))
        
        # Iterate over all the triples for the entity graph
        for (_, predicate, obj) in graph:
            # If the object is a URI to use a matching proxy instead
            if isinstance(obj, URIRef) and self.has_proxy(obj):
                obj = self.get_proxy_uri(obj)
            #  Add the triple to the proxy graph
            proxy_graph.add((proxy_uri, predicate, obj))
            
        #  Store the proxy graph in the triple store
        self._store_proxy(proxy_graph)
        
        # If a proxy was created update the other proxies that were referring
        # to the subject
        if created_proxy:
            self._relink_proxies(subject, proxy_uri)
    
        return proxy_uri.toPython()
    
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
        sparql = SPARQLWrapper(SPARQL)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        bindings = sparql.query().convert()["results"]["bindings"]
        if len(bindings) == 0:
            return None
        
        proxy = bindings[0]["proxy"]["value"]
        print ('Found the proxy {}'.format(proxy))
        return proxy
    
    def search(self, params):
        '''
        Full text search. The parameters are expected to contain a variable
        'q' with the text to be searched for.
        '''
        # Prepare the array of results
        results = []
        
        # Prepare the query
        query = self._queries['full_text_search.rq']
        query = query.replace("__TEXT__", params.get('q'))
        collection_name = params.get('collection', 'everything')
        query = query.replace("__COLLECTION__", BASE + collection_name)        
        logger.debug('Executing \n{}'.format(query))
        
        # Execute the query
        sparql = SPARQLWrapper(SPARQL)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        bindings = sparql.query().convert()["results"]["bindings"]
        
        # Convert the results
        for b in bindings:
            results.append(b["proxy"]["value"])
            
        return results
    
    def get_proxy(self, uri):
        '''
        Returns the description of a proxy entity
        '''
        logger.info('Get proxy data about {}'.format(uri))
        query = self._queries['get_proxy.rq'].replace("__URI__", uri)
        sparql = SPARQLWrapper(SPARQL)
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
        SELECT ?proxy WHERE {
            ?proxy owl:sameAs <__TARGET__>.
        }
        """.replace("__TARGET__", uri)
        sparql = SPARQLWrapper(SPARQL)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        bindings = sparql.query().convert()["results"]["bindings"]
        if len(bindings) > 0:
            return URIRef(bindings[0]["proxy"]["value"])
        else:
            return None
     
    def _store_proxy(self, graph):
        '''
        Insert the content of the graph into the triple store
        '''
        # TODO Use rdflib tricks to optimise that part
        query = """
        INSERT DATA {
            __PAYLOAD__
        }
        """.replace("__PAYLOAD__", graph.serialize(format="nt").decode())
        sparql = SPARQLWrapper(SPARUL)
        sparql.setQuery(query)
        sparql.setMethod(POST)
        sparql.query()
    
    def _relink_proxies(self, old_uri, new_uri):
        '''
        Update existing proxies to replace links to old_uri by links to new_uri
        '''
        # Prepare the new links
        query = """
        CONSTRUCT {
            ?proxy ?pred <__NEWURI__>.
        } WHERE {
            ?proxy ?pred <__OLDURI__>.
            FILTER (?proxy != <__NEWURI__>)
        }
        """.replace("__OLDURI__", old_uri).replace("__NEWURI__", new_uri)
        sparql = SPARQLWrapper(SPARQL)
        sparql.setQuery(query)
        graph = sparql.query().convert()
        
        # If there is nothing to do, return right away
        if len(graph) == 0:
            return
            
        # Remove all the old links
        query = """
        DELETE {
            ?proxy ?pred <__TARGET__>.
        } WHERE {
            ?proxy ?pred <__TARGET__>.
        }
        """.replace("__TARGET__", old_uri)
        sparql = SPARQLWrapper(SPARUL)
        sparql.setQuery(query)
        sparql.setMethod(POST)
        sparql.query()
        
        # Insert the new links
        query = """
        INSERT DATA {
            __PAYLOAD__
        }
        """.replace("__PAYLOAD__", graph.serialize(format="nt").decode())
        sparql = SPARQLWrapper(SPARUL)
        sparql.setQuery(query)
        sparql.setMethod(POST)
        sparql.query()
        
        # TODO handle merging proxies (?)
    
