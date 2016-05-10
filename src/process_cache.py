'''
Created on 8 May 2016

@author: guerec01
'''
from component.extractor import EntityExtractor
from storage.cache import CacheStore
from storage.proxy import ProxyStore
from storage.collection import CollectionStore
from urllib.parse import urlparse
from rdflib.namespace import RDF

import logging
LOG_FORMAT = "%(asctime)-15s [%(levelname)-7s] %(name)s : %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def process_entry(uri, cache, extractor, proxies, collections):
    '''
    Process one entry from the cache
    '''
    logger.info('Processing {}'.format(entry))

    # Retrieve the graph
    graph = cache.retrieve(uri)
    
    # Get it through the entity extraction
    entities = extractor.extract_entities(graph)

    # Store all those entities into the proxy store and update the collections
    for entity in entities:
        # Send that entity to the store
        proxy_uri = proxies.store(entity)
        
        # Add to the collection 'everything'
        collections.add_to_collection('everything', proxy_uri)
    
        # Add to the collection corresponding to its type
        subject = [s for s in entity.subjects()][0]
        proxy_type = entity.value(subject, RDF.type).toPython()
        if proxy_type in collections.TYPE_COLLECTIONS:
            (name, label, description) = collections.TYPE_COLLECTIONS[proxy_type]
            if not collections.contains(name):
                collections.create(name, label, description)
            collections.add_to_collection(name, proxy_uri)
            
        # Add to the collection for this source domain
        hostname = urlparse(entry).hostname
        name = hostname.replace('.','_')
        label = hostname
        description = 'Everything with data coming from {}'.format(hostname)
        if not collections.contains(name):
            collections.create(name, label, description)
        collections.add_to_collection(name, proxy_uri)
                
if __name__ == '__main__':
    # Create an instance of the entity extractor
    extractor = EntityExtractor()
    
    # Create an instance of the proxies interface
    proxies = ProxyStore()
    
    # Create an instance of the cache interface
    cache = CacheStore()
    
    # Create an instance of the collections interface
    collections = CollectionStore()
    
    # Get the list of cache entries to process
    entries = cache.get_processing_queue()
    
    # Process all the entries one by one
    for entry in entries:
        process_entry(entry, cache, extractor, proxies, collections)