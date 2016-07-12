'''
Created on 1 Apr 2016

@author: guerec01
'''
import datetime
import hashlib
from couchdb.client import Server
from couchdb import http
from rdflib.graph import Graph

import logging
logger = logging.getLogger(__name__)

def index_doc():
    '''
    This function returns the index used by CouchDB to search for metadata
    documents based on the URI of the graph they contain
    '''
    return  {
        "_id": "_design/index",
        "views": {
            "by_resource": {
                "map": """
                    function(doc) {
                    if ('@id' in doc) {
                        emit(doc['@id'], {'rev': doc._rev, 'g': doc._id})
                        }
                    }
                    """
            },
            "processing_queue": {
                "map": """
                    function(doc) {
                    if ('processed' in doc && !doc['processed']) {
                        emit(doc._id, doc['@id'])
                        }
                    }
                    """
            }
        }
    }

def filter_triples(graph):
    '''
    Utility function to remove triples that we don't need in the cache
    (essentially, literals not in Welsh or English)
    
    TODO: Implement this
    '''
    return graph

def get_identifier(uri):
    '''
    Utility function to turn a URI into an Hex identifier for CouchDB
    '''
    return hashlib.md5(uri.encode()).hexdigest()

class CacheStore(object):
    '''
    Interface to the data store containing all the cached resources
    '''
    def __init__(self, config, **client_opts):
        '''
        Constructor
        
        @param config: the Config object wrapping the configuration file
        '''
        # Get the config
        url = config.couchdb_url()
        self.db_name = config.couchdb_db()
        
        # Connect to CouchDB
        self._server = Server(url=url, **client_opts)
        
        # Initialise the DB if needed
        self._init_db()
    
    def _init_db(self):
        '''
        Initialise the DB if needed. Also add the index document if that one
        is not already there
        '''
        try:
            self._db = self._server[self.db_name]
        except http.ResourceNotFound:
            self._db = self._server.create(self.db_name)
            
        if not '_design/index' in self._db:
            self._db.save(index_doc())
        
    def reset_db(self):
        '''
        Clean the DB of its current content
        '''
        logger.info('Cleaning the content of the cache store')
        self._server.delete(self.db_name)
        self._init_db()
        
    def contains(self, uri):
        '''
        Returns True if the URI is already cached
        '''
        return len(self._db.view('index/by_resource', key=uri).rows) > 0

    def get_processing_queue(self):
        '''
        Returns the processing queue. This is the list of all the cache
        entries which have been marked as "processed = False" because they
        were updated or newly inserted
        '''
        queue = []
        for row in self._db.view('index/processing_queue').rows:
            queue.append(row.value)
        return queue
    
    def store(self, uri, graph):
        '''
        Store a given payload associated to a target resource URI.
        The actual operation performed is either an update or an insert
        depending if the resource was already cached or not
        '''
        # Generate an identifier based on the URI
        identifier = get_identifier(uri)
        
        # Filter out some triples from the graph
        filtered_graph = filter_triples(graph)
        
        # If the resource is already there fetch the previous metadata doc
        if self.contains(uri):
            metadata = self._db.get(identifier)
        else:
            metadata = {'_id': identifier, '@id': uri}
            
        # Update the metadata
        metadata['size'] = len(filtered_graph)
        metadata['last_updated'] = datetime.datetime.now().isoformat()
        metadata['processed'] = False

        # Save (insert or update) the metadata
        self._db.save(metadata)
        
        # Save the graph as a binary payload attached to the metadata
        self._db.put_attachment(metadata, filtered_graph.serialize(format='turtle'),
                                filename=identifier + '.ttl',
                                content_type='text/turtle')
    
    def retrieve(self, uri):
        '''
        Retrieve a graph from the cache
        '''
        logger.debug('Fetch {}'.format(uri))
        
        # Generate an identifier based on the URI
        identifier = get_identifier(uri)

        # Get the attached data and parse it
        data = self._db.get_attachment(identifier, filename=identifier + '.ttl').read()
        graph = Graph()
        graph.parse(data=data, format="turtle")
                
        # Return the graph
        return graph
