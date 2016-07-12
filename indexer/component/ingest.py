'''
Created on 8 Jul 2016

@author: guerec01
'''
from rdflib.graph import Dataset
from indexer.storage.cache import CacheStore

import logging
logger = logging.getLogger(__name__)

class Ingest(object):
    '''
    This class provides the higher level interface to the cache store
    '''
    def __init__(self, config, clean=False):
        '''
        Constructor
        '''
        # Get an instance of the cache interface
        self.cache = CacheStore(config)
    
        # If we want to clean the DB, do it
        if clean:
            self.cache.reset_db()
            
    def load(self, nquad_file_name):
        '''
        Load the content of an NQuad file into the cache
        '''
        logger.info('Loading {}'.format(nquad_file_name))
        
        # Load the NQuads
        g = Dataset()
        g.parse(nquad_file_name, format='nquads')
        
        # For each graph in the dataset
        for graph in g.graphs():
            uri = graph.identifier
            if uri.startswith('http://'):
                # Push the graph to the cache
                logger.info('Found graph {}'.format(uri))
                self.cache.store(uri, g.graph(graph))
