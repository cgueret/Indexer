#!/usr/bin/python3
'''
Created on 8 Jul 2016

Command line interface to Indexer. Let admins perform essential functions
such as ingesting NQuads or adding new URIs to the crawling queue

@author: guerec01
'''
import argparse
from argparse import RawTextHelpFormatter

import logging
logger = logging.getLogger(__file__)

from indexer.util.config import Config
from indexer.component.ingest import Ingest
from indexer.component.process import Process
from indexer.storage.cache import CacheStore

COMMANDS="""
Commands:
    ingest FILE.NQ
        Ingest the content of FILE.NQ into Indexer
    process
        Process the content of the queue
"""

def init_login(debug=False):
    LOG_FORMAT = "%(asctime)-15s [%(levelname)-7s] %(name)s : %(message)s"
    logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG if debug else logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("rdflib").setLevel(logging.WARNING)
    
def ingest(config, nquad_file_name, clean=False):
    '''
    Ingest the content of the NQuads file passed as parameter
    
    @param nquad_file_name: the file name to ingest
    @param clean: if True clean the cache DB before ingesting
    '''
    logger.info('Ingesting {}'.format(nquad_file_name))
    ingest = Ingest(config, clean)
    ingest.load(nquad_file_name)

def process(config, clean=False):
    '''
    Get the list of cached entries to be processed and process all of them
    one after the other

    @param clean: if True clean the proxy and collection DB before processing
    '''
    logger.info('Start processing the queue')
    
    # Get the list of cache entries to process
    cache = CacheStore(config)
    entries = cache.get_processing_queue()
    logger.info('{} entries to process'.format(len(entries)))
    
    # Create an instance of the data processor and process all the entries one by one
    processor = Process(config, clean)
    for entry in entries:
        processor.process(entry)
    
if __name__ == '__main__':
    # Parse the command line arguments
    parser = argparse.ArgumentParser(
        description='Command line interface to Indexer',
        epilog=COMMANDS,
        formatter_class=RawTextHelpFormatter)
    parser.add_argument('command', type=str, nargs=1, help='command to perform')
    parser.add_argument('param', type=str, nargs='*',
                        help='parameters to use for the command')
    parser.add_argument('-c', dest='file', default='config.cfg', 
                        help='configuration file')
    parser.add_argument('--clean', action='store_true',
                        help='Clean the relevant DB(s) before performing the command')
    parser.add_argument('--debug', action='store_true',
                        help='Switch debugging on (overrides the config file value)')
    args = parser.parse_args()
    
    # Load the configuration file
    config = Config(args.file)
    init_login(args.debug)

    # Execute the command
    if args.command[0] == 'ingest':
        ingest(config, args.param[0], args.clean)
    elif args.command[0] == 'process':
        process(config, args.clean)
    else:
        parser.print_help()
