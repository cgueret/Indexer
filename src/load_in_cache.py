'''
Created on 1 Apr 2016

Load a set of NQuads files into the cache
  
@author: guerec01
'''
import argparse
from rdflib.graph import Dataset
from storage.cache import CacheStore

def process_files(nquad_files):
    '''
    Process an array of target NQuad files
    
    @param nquad_files: an array of file paths
    '''
    # Get an instance of the cache interface
    cache = CacheStore()
    
    # Iterate over the array
    for nquad_file in nquad_files:
        print ('Processing {}'.format(nquad_file))
        g = Dataset()
        g.parse(nquad_file, format='nquads')
        for graph in g.graphs():
            uri = graph.identifier
            if uri.startswith('http://'):
                print ('Found graph {}'.format(uri))
                cache.store(uri, g.graph(graph))
                
if __name__ == '__main__':
    # Parse the command line arguments
    parser = argparse.ArgumentParser(description='Ingest a set of resources')
    parser.add_argument('nquads', metavar='file.nq', type=str, nargs='+',
                        help='an nquad dump to ingest')
    args = parser.parse_args()
    
    # Process the requested files
    process_files(args.nquads)
