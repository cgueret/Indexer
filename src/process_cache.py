'''
Created on 8 May 2016

@author: guerec01
'''
from component.extractor import EntityExtractor
from storage.cache import CacheStore
from storage.proxy import ProxyStore

def process_entry(uri, cache, extractor, proxies):
    print ('Processing {}'.format(entry))

    # Retrieve the graph
    graph = cache.retrieve(uri)
    
    # Get it through the entity extraction
    entities = extractor.extract_entities(graph)

    # Store all those entities into the proxy store
    for entity in entities:
        proxies.store(entity)
        
    # Update the collections
    
if __name__ == '__main__':
    # Create an instance of the entity extractor
    extractor = EntityExtractor()
    
    # Create an instance of the proxies interface
    proxies = ProxyStore()
    
    # Create an instance of the cache interface
    cache = CacheStore()
    
    # Get the list of cache entries to process
    entries = cache.get_processing_queue()
    
    # Process all the entries one by one
    for entry in entries:
        process_entry(entry, cache, extractor, proxies)